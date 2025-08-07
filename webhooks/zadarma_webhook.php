<?php
// ВИПРАВЛЕНИЙ zadarma_webhook.php з правильним роутингом
// ✅ IVR та Bot розділені
// ✅ Використовує simple_webhook.py з правильною логікою

error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('log_errors', 1);
ini_set('error_log', 'error_log');

header('Content-Type: application/json; charset=utf-8');

function writeLog($message) {
    error_log(date('[d-M-Y H:i:s T]') . ' ' . $message);
}

// GET запит для валідації webhook
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (isset($_GET['zd_echo'])) {
        echo $_GET['zd_echo'];
        exit;
    }
    
    echo json_encode([
        'status' => 'active',
        'message' => 'Zadarma Webhook працює',
        'time' => date('Y-m-d H:i:s'),
        'version' => 'fixed_v1.0'
    ]);
    exit;
}

// POST запит - обробка webhook
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    
    // Отримуємо дані
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    // Якщо JSON не спрацював, пробуємо POST
    if (!$data) {
        $data = $_POST;
    }
    
    writeLog("Zadarma webhook received: " . json_encode($data));
    
    $event = $data['event'] ?? '';
    $caller_id = $data['caller_id'] ?? '';
    $called_did = $data['called_did'] ?? '';
    
    // ✅ ПРАВИЛЬНИЙ РОУТИНГ - визначаємо чи це бот чи IVR
    $is_bot_callback = isBotCallback($caller_id, $called_did);
    
    writeLog("Bot callback check: FROM=$caller_id, TO=$called_did, IS_BOT=" . ($is_bot_callback ? 'YES' : 'NO'));
    
    if ($is_bot_callback) {
        // ✅ РОУТИНГ ДО PYTHON БОТА - використовуємо simple_webhook.py
        writeLog("ROUTING TO PYTHON BOT");
        $result = routeToPythonBot($data);
        echo json_encode(['status' => 'bot_processed', 'result' => $result]);
    } else {
        // ✅ РОУТИНГ ДО IVR - обробляємо в PHP
        writeLog("ROUTING TO IVR");
        $result = routeToIVR($data);
        echo $result;
    }
    
} else {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
}

function isBotCallback($caller_id, $called_did) {
    /**
     * Визначає чи це callback від бота чи звичайний IVR дзвінок
     * 
     * Bot callback ознаки:
     * - FROM = основний номер клініки (0733103110)
     * - TO = номер пристрою (хвіртка/ворота)
     */
    
    $clinic_number = '0733103110';
    $device_numbers = ['0637442017', '0930063585'];
    
    // Нормалізуємо номери (прибираємо префікси)
    $caller_clean = preg_replace('/^(\+38|38|8)?0?/', '0', $caller_id);
    $called_clean = preg_replace('/^(\+38|38|8)?0?/', '0', $called_did);
    
    // Перевіряємо чи дзвінок йде З клініки НА пристрій
    $from_clinic = ($caller_clean === $clinic_number);
    $to_device = in_array($called_clean, $device_numbers);
    
    return $from_clinic && $to_device;
}

function routeToPythonBot($data) {
    /**
     * Відправляє webhook дані до Python бота для обробки
     */
    
    $json = escapeshellarg(json_encode($data, JSON_UNESCAPED_UNICODE));
    
    // ✅ ВИКОРИСТОВУЄМО simple_webhook.py з правильною логікою
    $command = "cd /home/gomoncli/zadarma && /usr/bin/python3 simple_webhook.py $json 2>&1";
    
    $output = shell_exec($command);
    $exit_code = 0;
    
    writeLog("Python result (code $exit_code): $output");
    
    return trim($output);
}

function routeToIVR($data) {
    /**
     * Обробляє IVR логіку для звичайних дзвінків
     */
    
    $event = $data['event'] ?? '';
    
    switch ($event) {
        case 'NOTIFY_START':
            return handleIVRStart($data);
            
        case 'NOTIFY_IVR':
            return handleIVRResponse($data);
            
        case 'NOTIFY_END':
            return handleIVREnd($data);
            
        default:
            return json_encode(['status' => 'ok', 'message' => 'Event ignored']);
    }
}

function handleIVRStart($data) {
    /**
     * Обробляє початок IVR дзвінка - показує головне меню
     */
    
    $caller_id = $data['caller_id'] ?? 'Unknown';
    writeLog("IVR Start from: $caller_id");
    
    return json_encode([
        'ivr_say' => [
            'text' => 'Доброго дня! Ви дзвоните до системи контролю доступу клініки. Натисніть 1 для відкриття воріт, 2 для відкриття хвіртки, або зачекайте для зв\'язку з адміністратором.',
            'language' => 'ua'
        ],
        'wait_dtmf' => [
            'timeout' => 15,
            'max_digits' => 1,
            'attempts' => 3,
            'name' => 'main_menu'
        ]
    ]);
}

function handleIVRResponse($data) {
    /**
     * Обробляє відповідь користувача в IVR
     */
    
    $caller_id = $data['caller_id'] ?? 'Unknown';
    $wait_dtmf = $data['wait_dtmf'] ?? [];
    $digits = $wait_dtmf['digits'] ?? '';
    
    writeLog("IVR Response from $caller_id: '$digits'");
    
    switch ($digits) {
        case '1':
            // Запит на відкриття воріт
            return json_encode([
                'ivr_say' => [
                    'text' => 'Ви вибрали відкриття воріт. Зачекайте, будь ласка, перевіряємо доступ.',
                    'language' => 'ua'
                ],
                'hangup' => true
            ]);
            
        case '2':
            // Запит на відкриття хвіртки  
            return json_encode([
                'ivr_say' => [
                    'text' => 'Ви вибрали відкриття хвіртки. Зачекайте, будь ласка, перевіряємо доступ.',
                    'language' => 'ua'
                ],
                'hangup' => true
            ]);
            
        default:
            // Невірний вибір або таймаут - переводимо до адміністратора
            return json_encode([
                'ivr_say' => [
                    'text' => 'Переводимо вас до адміністратора.',
                    'language' => 'ua'
                ],
                'redirect' => [
                    'to' => '102'  // Внутрішній номер адміністратора
                ]
            ]);
    }
}

function handleIVREnd($data) {
    /**
     * Обробляє завершення IVR дзвінка
     */
    
    $caller_id = $data['caller_id'] ?? 'Unknown';
    $duration = $data['duration'] ?? 0;
    
    writeLog("IVR End from $caller_id (duration: {$duration}s)");
    
    return json_encode(['status' => 'ok']);
}

?>
