<?php
// ДІАГНОСТИКА ЗВУКУ - різні варіанти програвання
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
    
    'sound_files' => [
        'gate_laura' => '687a8e0c3490bc1c2c043ce5',    
        'door_laura' => '687a8e13a7987a5ca70a4eb7',    
        'telegram_laura' => '687a8e1bf70280c1a109b34c'
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
        'message' => 'SOUND DEBUG VERSION',
        'version' => '7.1-sound-debug',
        'tests' => [
            'test1' => 'ivr_play + hangup',
            'test2' => 'ivr_play без hangup',
            'test3' => 'ivr_saypopular',
            'test4' => 'ivr_saydigits'
        ]
    ], JSON_PRETTY_PRINT);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true) ?: $_POST;
    
    writeLog("=== SOUND DEBUG ===");
    writeLog("Input: $input");
    
    $event = $data['event'] ?? '';
    $caller_id = normalizePhoneNumber($data['caller_id'] ?? 'Unknown');
    $internal = $data['internal'] ?? '';
    
    if ($event === 'NOTIFY_INTERNAL') {
        handleSoundTest($internal, $caller_id);
    } else {
        echo json_encode(['status' => 'ok']);
    }
}

function handleSoundTest($internal, $caller_id) {
    global $config;
    
    writeLog("🎵 SOUND TEST: Internal $internal, Caller $caller_id");
    
    // Спробуємо різні варіанти звуку залежно від номера
    switch ($internal) {
        case '201':
            // ТЕСТ 1: Стандартний ivr_play + hangup
            writeLog("TEST 1: ivr_play + hangup");
            
            $response = [
                'ivr_play' => $config['sound_files']['door_laura'],
                'hangup' => true
            ];
            
            makeCallback($config['door_number'], $config, $caller_id);
            break;
            
        case '202':
            // ТЕСТ 2: ivr_play без hangup
            writeLog("TEST 2: ivr_play без hangup");
            
            $response = [
                'ivr_play' => $config['sound_files']['gate_laura']
            ];
            
            makeCallback($config['gate_number'], $config, $caller_id);
            break;
            
        case '203':
            // ТЕСТ 3: ivr_saypopular (популярна фраза)
            writeLog("TEST 3: ivr_saypopular");
            
            $response = [
                'ivr_saypopular' => 5,  // "Ласкаво просимо"
                'language' => 'ua',
                'hangup' => true
            ];
            break;
            
        case '204':
            // ТЕСТ 4: ivr_saydigits
            writeLog("TEST 4: ivr_saydigits");
            
            $response = [
                'ivr_saydigits' => '1234',
                'language' => 'ua',
                'hangup' => true
            ];
            break;
            
        case '205':
            // ТЕСТ 5: Комбінований (спочатку звук, потім hangup через 3 сек)
            writeLog("TEST 5: Комбінований звук");
            
            $response = [
                'ivr_play' => $config['sound_files']['telegram_laura'],
                'wait_dtmf' => [
                    'timeout' => 3,
                    'attempts' => 1,
                    'maxdigits' => 1,
                    'name' => 'sound_test',
                    'default' => 'hangup'
                ]
            ];
            break;
            
        default:
            writeLog("Невідомий internal: $internal");
            $response = ['status' => 'ok'];
            break;
    }
    
    writeLog("Response: " . json_encode($response));
    echo json_encode($response);
}

function makeCallback($toNumber, $config, $caller_id) {
    writeLog("Callback: {$config['main_phone']} → $toNumber");
    
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
    
    $headers = ['Authorization: ' . $config['zadarma_key'] . ':' . $signature];
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
    
    writeLog("Callback: HTTP $httpCode, Response: $response");
}
?>
