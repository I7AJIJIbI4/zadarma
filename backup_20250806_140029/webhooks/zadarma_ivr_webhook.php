<?php
// ОНОВЛЕНА СИСТЕМА з IVR + Telegram Bot Support
header('Content-Type: application/json; charset=utf-8');

if (isset($_GET['zd_echo'])) {
    exit($_GET['zd_echo']);
}

$config = [
    'zadarma_key' => '322168f1b94be856f0de',
    'zadarma_secret' => 'ae4b189367a9f6de88b3',
    'main_phone' => '0733103110',
    'gate_number' => '0930063585',
    'door_number' => '0637442017',
    'log_file' => '/home/gomoncli/zadarma/ivr_webhook.log',

    // SMS-Fly з правильним відправником
    'sms_api_key' => 'pJYAWmZpWOvUozqAUvsTaBjxTpu9oJEk',
    'sms_api_url' => 'https://sms-fly.ua/api/v2/api.php',
    'sms_source' => 'Dr. Gomon', // ВИПРАВЛЕНО: з пробілом
    'sms_message' => 'Щоб отримати простий спосіб доступу до Dr. Gomon Cosmetology скористайтесь нашим консьєрж ботом - https://t.me/DrGomonConciergeBot',

    'internal_numbers' => [
        '201' => ['name' => 'IVR Хвіртка', 'action' => 'open_door', 'target' => '0637442017'],
        '202' => ['name' => 'IVR Ворота', 'action' => 'open_gate', 'target' => '0930063585'],
        '203' => ['name' => 'IVR SMS', 'action' => 'send_sms', 'target' => null],
        '101' => ['name' => 'Прямо Хвіртка', 'action' => 'open_door', 'target' => '0637442017'],
        '102' => ['name' => 'Прямо Ворота', 'action' => 'open_gate', 'target' => '0930063585'],
        '103' => ['name' => 'Прямо SMS', 'action' => 'send_sms', 'target' => null]
    ],

    'telegram_config' => [
        'bot_token' => '8030228734:AAGYMKVWYfNT5h-UJlVWmmWmul8-KhdaOk4',
        'chat_id' => '573368771'
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

function formatPhoneForSMS($phone) {
    $phone = preg_replace('/[^\d]/', '', $phone);

    if (substr($phone, 0, 3) === '380') {
        return $phone;
    } elseif (substr($phone, 0, 2) === '80') {
        return '3' . $phone;
    } elseif (substr($phone, 0, 1) === '0') {
        return '38' . $phone;
    }

    return '380' . $phone;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    echo json_encode([
        'status' => 'active',
        'message' => '🚀 FINAL WORKING SYSTEM + TELEGRAM BOT',
        'version' => '18.0-TELEGRAM-INTEGRATION',
        'sms_source' => 'Dr. Gomon (з пробілом)',
        'features' => [
            'door_control' => 'Zadarma Callback ✅',
            'gate_control' => 'Zadarma Callback ✅',
            'sms_delivery' => 'SMS-Fly API ✅',
            'telegram_backup' => 'Available ✅',
            'telegram_bot_integration' => 'НОВИНКА ✅'
        ]
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $data = json_decode(file_get_contents('php://input'), true) ?: $_POST;

    writeLog("WEBHOOK RECEIVED: " . json_encode($data));

    $event = $data['event'] ?? '';
    $caller_id = normalizePhoneNumber($data['caller_id'] ?? 'Unknown');
    $internal = $data['internal'] ?? '';

    // ОБРОБКА РІЗНИХ ТИПІВ ПОДІЙ
    if ($event === 'NOTIFY_INTERNAL') {
        // Існуюча IVR система
        handleCorrectSource($internal, $caller_id);
    } elseif ($event === 'NOTIFY_START' || $event === 'NOTIFY_END') {
        // НОВИНКА: Обробка подій для телеграм бота
        handleTelegramBotEvent($data);
    } else {
        writeLog("ℹ️ Event $event ignored");
        echo json_encode(['status' => 'ok']);
    }
}

// НОВИНКА: Функція для обробки подій телеграм бота
function handleTelegramBotEvent($data) {
    writeLog("🤖 TELEGRAM BOT EVENT: " . json_encode($data));
    
    $event = $data['event'] ?? '';
    $pbxCallId = $data['pbx_call_id'] ?? '';
    $disposition = $data['disposition'] ?? '';
    
    // Викликаємо Python скрипт для обробки
    if (in_array($event, ['NOTIFY_START', 'NOTIFY_END'])) {
        $pythonScript = '/home/gomoncli/zadarma/process_webhook.py';
        $jsonData = escapeshellarg(json_encode($data));
        
        $command = "cd /home/gomoncli/zadarma && python3 $pythonScript $jsonData 2>&1";
        
        writeLog("🐍 Executing Python: $command");
        
        $output = shell_exec($command);
        $exitCode = shell_exec("echo $?");
        
        writeLog("📤 Python output: " . ($output ?: 'No output'));
        writeLog("📊 Python exit code: " . ($exitCode ?: 'Unknown'));
        
        if ($exitCode == 0) {
            writeLog("✅ Telegram bot event processed successfully");
        } else {
            writeLog("❌ Telegram bot event processing failed");
        }
    }
    
    echo json_encode(['status' => 'ok']);
}

// Існуюча функція IVR системи
function handleCorrectSource($internal, $caller_id) {
    global $config;

    writeLog("🚀 IVR SYSTEM: Internal $internal, Caller $caller_id");

    if (isset($config['internal_numbers'][$internal])) {
        $internal_config = $config['internal_numbers'][$internal];
        $name = $internal_config['name'];
        $action = $internal_config['action'];
        $target = $internal_config['target'];

        switch ($action) {
            case 'open_door':
                writeLog("🏠 ХВІРТКА");
                                $result = makeCallbackWithTracking($target, $config, $caller_id, "hvirtka");
                                if ($result === "pending") {
                    writeLog("📞 Хвіртка: очікуємо webhook підтвердження...");
                } else {
                    writeLog("❌ Помилка API для хвіртки");
                }
                break;

            case 'open_gate':
                writeLog("🚪 ВОРОТА");
                                $result = makeCallbackWithTracking($target, $config, $caller_id, "vorota");
                                if ($result === "pending") {
                    writeLog("📞 Ворота: очікуємо webhook підтвердження...");
                } else {
                    writeLog("❌ Помилка API для воріт");
                }
                break;

            case 'send_sms':
                writeLog("📱 SMS з правильним відправником 'Dr. Gomon'");
                $success = sendSMSFlyFinal($caller_id, $config['sms_message'], $config);
                writeLog($success ? "✅ SMS успішно надіслано" : "❌ SMS помилка");

                if (!$success) {
                    writeLog("📱 Backup Telegram");
                    sendTelegramBackup($caller_id, $config);
                }
                break;
        }
    }

    echo json_encode(['status' => 'ok']);
}

function sendSMSFlyFinal($phone, $message, $config) {
    writeLog("📱 SMS-Fly FINAL: з правильним відправником");

    $formatted_phone = formatPhoneForSMS($phone);
    writeLog("📱 SMS-Fly FINAL: номер $formatted_phone, відправник '{$config['sms_source']}'");

    $url = $config['sms_api_url'];

    $request_data = [
        'auth' => [
            'key' => $config['sms_api_key']
        ],
        'action' => 'SENDMESSAGE',
        'data' => [
            'recipient' => $formatted_phone,
            'channels' => ['sms'],
            'sms' => [
                'source' => $config['sms_source'], // "Dr. Gomon" з пробілом
                'text' => $message,
                'start_time' => 'AUTO'
            ]
        ]
    ];

    $json_data = json_encode($request_data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    writeLog("📱 SMS-Fly FINAL request: $json_data");

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $json_data);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json; charset=utf-8',
        'Accept: application/json'
    ]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    writeLog("📱 SMS-Fly FINAL: HTTP $httpCode, Response: $response");

    if ($httpCode === 200) {
        $result = json_decode($response, true);

        if (isset($result['success']) && $result['success'] == 1) {
            writeLog("🎉 SMS-Fly SUCCESS! Повідомлення надіслано успішно");
            return true;
        } else {
            $error_desc = $result['error']['description'] ?? json_encode($result);
            writeLog("❌ SMS-Fly error: $error_desc");
        }
    }

    return false;
}

function makeCallback($toNumber, $config, $caller_id) {
    writeLog("📞 Callback: {$config['main_phone']} → $toNumber");

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

    writeLog("📞 Callback result: HTTP $httpCode");
    return $httpCode === 200 && strpos($response, '"status":"success"') !== false;
}

function makeCallbackWithTracking($toNumber, $config, $caller_id, $action_type) {
    writeLog("📞 Callback з відстеженням: {$config['main_phone']} → $toNumber");
    
    // 1. Створити унікальний ID для відстеження
    $call_id = "ivr_" . time() . "_" . preg_replace('/[^\d]/', '', $caller_id);
    
    // 2. Підготувати дані для відстеження
    $tracking_data = [
        'call_id' => $call_id,
        'target_number' => $toNumber,
        'caller_id' => $caller_id,
        'action_type' => $action_type,
        'timestamp' => time(),
        'status' => 'pending'
    ];
    
    // 3. Зберегти в тимчасовий файл для webhook
    $pending_file = '/tmp/pending_ivr_calls.json';
    $existing_data = [];
    
    if (file_exists($pending_file)) {
        $content = file_get_contents($pending_file);
        $existing_data = json_decode($content, true) ?: [];
    }
    
    $existing_data[] = $tracking_data;
    file_put_contents($pending_file, json_encode($existing_data, JSON_PRETTY_PRINT));
    
    writeLog("📋 Зареєстровано для відстеження: $call_id");
    
    // 4. Зробити API запит
    $api_success = makeCallback($toNumber, $config, $caller_id);
    
    if ($api_success) {
        writeLog("📞 API callback успішний, очікуємо webhook підтвердження...");
        return 'pending';
    } else {
        writeLog("❌ Помилка API callback");
        // Видалити з pending списку
        removePendingCall($call_id);
        return false;
    }
}

function removePendingCall($call_id) {
    $pending_file = '/tmp/pending_ivr_calls.json';
    if (file_exists($pending_file)) {
        $content = file_get_contents($pending_file);
        $data = json_decode($content, true) ?: [];
        
        $data = array_filter($data, function($item) use ($call_id) {
            return $item['call_id'] !== $call_id;
        });
        
        file_put_contents($pending_file, json_encode(array_values($data), JSON_PRETTY_PRINT));
    }
}

function getPendingCallByTarget($target_number, $max_age_seconds = 120) {
    $pending_file = '/tmp/pending_ivr_calls.json';
    if (!file_exists($pending_file)) {
        return null;
    }
    
    $content = file_get_contents($pending_file);
    $data = json_decode($content, true) ?: [];
    
    $current_time = time();
    
    foreach ($data as $call) {
        if ($call['target_number'] === $target_number && 
            ($current_time - $call['timestamp']) <= $max_age_seconds &&
            $call['status'] === 'pending') {
            return $call;
        }
    }
    
    return null;
}

function updatePendingCallStatus($call_id, $status) {
    $pending_file = '/tmp/pending_ivr_calls.json';
    if (!file_exists($pending_file)) {
        return false;
    }
    
    $content = file_get_contents($pending_file);
    $data = json_decode($content, true) ?: [];
    
    foreach ($data as &$call) {
        if ($call['call_id'] === $call_id) {
            $call['status'] = $status;
            $call['completed_at'] = time();
            break;
        }
    }
    
    file_put_contents($pending_file, json_encode($data, JSON_PRETTY_PRINT));
    return true;
}

function sendTelegramBackup($caller_id, $config) {
    $message = "🚨 SMS BACKUP\n📞 Дзвінок: $caller_id\n🕐 " . date('Y-m-d H:i:s') . "\n\n" . $config['sms_message'];

    $url = "https://api.telegram.org/bot{$config['telegram_config']['bot_token']}/sendMessage";
    $data = ['chat_id' => $config['telegram_config']['chat_id'], 'text' => $message];

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
