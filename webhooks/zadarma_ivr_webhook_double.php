<?php
// ПОДВІЙНИЙ API ПІДХІД: IVR звук + Callback дзвінок
header('Content-Type: application/json; charset=utf-8');

if (isset($_GET['zd_echo'])) {
    exit($_GET['zd_echo']);
}

$config = [
    'zadarma_key' => '322168f1b94be856f0de',
    'zadarma_secret' => 'ae4b189367a9f6de88b3',
    'main_phone' => '0733103110',
    'gate_number' => '0930063585',
    'door_number' => '0933297777',
    'log_file' => '/home/gomoncli/zadarma/ivr_webhook.log',
    
    // Звукові файли
    'sound_files' => [
        'door_laura' => '687a8e13a7987a5ca70a4eb7',
        'gate_laura' => '687a8e0c3490bc1c2c043ce5',
        'telegram_laura' => '687a8e1bf70280c1a109b34c'
    ],
    
    'internal_numbers' => [
        '201' => ['name' => 'IVR Хвіртка', 'action' => 'door_with_sound', 'sound' => 'door_laura', 'target' => '0933297777'],
        '202' => ['name' => 'IVR Ворота', 'action' => 'gate_with_sound', 'sound' => 'gate_laura', 'target' => '0930063585'],
        '203' => ['name' => 'IVR Telegram', 'action' => 'telegram_with_sound', 'sound' => 'telegram_laura', 'target' => null],
        '101' => ['name' => 'Прямо Хвіртка', 'action' => 'door_direct', 'sound' => null, 'target' => '0933297777'],
        '102' => ['name' => 'Прямо Ворота', 'action' => 'gate_direct', 'sound' => null, 'target' => '0930063585']
    ]
];

function writeLog($message) {
    global $config;
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($config['log_file'], "[$timestamp] $message\n", FILE_APPEND | LOCK_EX);
}

function normalizePhoneNumber($phone) {
    $phone = preg_replace('/[^\d]/', '', $phone);
    if (substr($phone, 0, 3) === '380') {
        return substr($phone, 2);
    } elseif (substr($phone, 0, 2) === '80') {
        return '0' . substr($phone, 2);
    }
    return $phone;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    echo json_encode([
        'status' => 'active',
        'message' => 'DOUBLE API: Sound API + Callback API',
        'version' => '11.0-double-api',
        'approach' => 'Два окремі API виклики замість webhook відповіді'
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true) ?: $_POST;
    
    writeLog("DOUBLE API: " . json_encode($data));
    
    $event = $data['event'] ?? '';
    $caller_id = normalizePhoneNumber($data['caller_id'] ?? 'Unknown');
    $internal = $data['internal'] ?? '';
    $pbx_call_id = $data['pbx_call_id'] ?? '';
    
    if ($event === 'NOTIFY_INTERNAL') {
        handleDoubleAPI($internal, $caller_id, $pbx_call_id);
    } else {
        echo json_encode(['status' => 'ok']);
    }
}

function handleDoubleAPI($internal, $caller_id, $pbx_call_id) {
    global $config;
    
    writeLog("🔄 DOUBLE API: Internal $internal, Caller $caller_id, PBX: $pbx_call_id");
    
    // Захист від петель
    if ($caller_id === $config['gate_number'] || $caller_id === $config['door_number']) {
        writeLog("🛡️ Захист від петлі");
        echo json_encode(['status' => 'ok']);
        return;
    }
    
    if (isset($config['internal_numbers'][$internal])) {
        $internal_config = $config['internal_numbers'][$internal];
        $name = $internal_config['name'];
        $action = $internal_config['action'];
        $sound = $internal_config['sound'];
        $target = $internal_config['target'];
        
        writeLog("🎯 $name - подвійний API виклик");
        
        // КРОК 1: Відправляємо звук (якщо є)
        if ($sound && isset($config['sound_files'][$sound])) {
            $soundResult = sendSoundAPI($pbx_call_id, $config['sound_files'][$sound], $config);
            writeLog($soundResult ? "🎵 Звук API успішний" : "❌ Звук API помилка");
        }
        
        // КРОК 2: Відправляємо callback
        if ($target) {
            $callbackResult = makeZadarmaCallback($target, $config, $caller_id);
            writeLog($callbackResult ? "📞 Callback API успішний" : "❌ Callback API помилка");
        }
        
        // КРОК 3: Telegram (якщо потрібно)
        if (strpos($action, 'telegram') !== false) {
            $telegramResult = sendTelegram($caller_id, $config);
            writeLog($telegramResult ? "📱 Telegram API успішний" : "❌ Telegram API помилка");
        }
    }
    
    // Відповідаємо звичайним статусом
    echo json_encode(['status' => 'ok']);
}

function sendSoundAPI($pbx_call_id, $sound_file_id, $config) {
    writeLog("🎵 Sound API: PBX $pbx_call_id, File: $sound_file_id");
    
    // Спробуємо різні API endpoints для програвання звуку
    $endpoints = [
        '/v1/pbx/ivr/play/',
        '/v1/pbx/play/',
        '/v1/ivr/play/'
    ];
    
    foreach ($endpoints as $method) {
        writeLog("Trying sound endpoint: $method");
        
        $params = [
            'pbx_call_id' => $pbx_call_id,
            'ivr_play' => $sound_file_id,
            'format' => 'json'
        ];
        
        ksort($params);
        $paramsString = http_build_query($params);
        $stringToSign = $method . $paramsString . md5($paramsString);
        $signature = base64_encode(hash_hmac('sha1', $stringToSign, $config['zadarma_secret'], false));
        
        $headers = [
            'Authorization: ' . $config['zadarma_key'] . ':' . $signature,
            'Content-Type: application/x-www-form-urlencoded'
        ];
        
        $url = 'https://api.zadarma.com' . $method;
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $paramsString);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        writeLog("Sound API $method: HTTP $httpCode, Response: $response");
        
        if ($httpCode === 200) {
            $result = json_decode($response, true);
            if (($result['status'] ?? '') === 'success') {
                return true;
            }
        }
    }
    
    return false;
}

function makeZadarmaCallback($toNumber, $config, $fromCaller) {
    writeLog("📞 Callback API: {$config['main_phone']} → $toNumber");
    
    $method = '/v1/request/callback/';
    $params = [
        'from' => $config['main_phone'],
        'to' => $toNumber,
        'format' => 'json'
    ];
    
    ksort($params);
    $paramsString = http_build_query($params);
    $stringToSign = $method . $paramsString . md5($paramsString);
    $signature = base64_encode(hash_hmac('sha1', $stringToSign, $config['zadarma_secret'], false));
    
    $headers = [
        'Authorization: ' . $config['zadarma_key'] . ':' . $signature,
        'Content-Type: application/x-www-form-urlencoded'
    ];
    
    $url = 'https://api.zadarma.com' . $method . '?' . $paramsString;
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    writeLog("Callback API result: HTTP $httpCode, Response: $response");
    
    if ($httpCode === 200) {
        $result = json_decode($response, true);
        return ($result['status'] ?? '') === 'success';
    }
    
    return false;
}

function sendTelegram($caller_id, $config) {
    writeLog("📱 Telegram API для: $caller_id");
    
    $message = "🚨 ТРИГЕР!\n📞 Дзвінок: $caller_id\n🕐 Час: " . date('Y-m-d H:i:s');
    
    $url = "https://api.telegram.org/bot8030228734:AAGYMKVWYfNT5h-UJlVWmmWmul8-KhdaOk4/sendMessage";
    $data = ['chat_id' => '573368771', 'text' => $message];
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    return $httpCode === 200;
}
?>
