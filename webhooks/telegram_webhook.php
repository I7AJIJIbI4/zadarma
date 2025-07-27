<?php
/**
 * telegram_webhook.php - Webhook для інтеграції з телеграм ботом
 * Розміщується в: /home/gomoncli/public_html/telegram_webhook.php
 * 
 * Цей файл викликає Python функцію для обробки webhook даних
 * і забезпечує зв'язок між Zadarma webhook та телеграм ботом
 */

header('Content-Type: application/json');

// Логування
function writeLog($message) {
    $timestamp = date('Y-m-d H:i:s');
    $logMessage = "[$timestamp] $message" . PHP_EOL;
    file_put_contents('/home/gomoncli/zadarma/telegram_webhook.log', $logMessage, FILE_APPEND | LOCK_EX);
}

try {
    writeLog("🔔 Telegram webhook called");
    
    // Отримання даних з POST запиту
    $input = file_get_contents('php://input');
    
    if (empty($input)) {
        writeLog("⚠️ Empty request");
        echo json_encode(['status' => 'error', 'message' => 'Empty request']);
        exit;
    }
    
    writeLog("📥 Received data: " . $input);
    
    // Парсинг JSON
    $webhookData = json_decode($input, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        writeLog("❌ JSON error: " . json_last_error_msg());
        echo json_encode(['status' => 'error', 'message' => 'Invalid JSON']);
        exit;
    }
    
    $event = $webhookData['event'] ?? '';
    
    // Обробляємо тільки потрібні події
    if (in_array($event, ['NOTIFY_START', 'NOTIFY_END'])) {
        writeLog("📞 Processing event: $event");
        
        // Викликаємо Python скрипт для обробки
        $pythonScript = '/home/gomoncli/zadarma/process_webhook.py';
        $jsonData = escapeshellarg($input);
        
        $command = "cd /home/gomoncli/zadarma && python3 $pythonScript $jsonData 2>&1";
        
        writeLog("🐍 Executing Python: $command");
        
        $output = shell_exec($command);
        $exitCode = shell_exec("echo $?");
        
        writeLog("📤 Python output: " . ($output ?: 'No output'));
        writeLog("📊 Exit code: " . ($exitCode ?: 'Unknown'));
        
        if ($exitCode == 0) {
            writeLog("✅ Python script executed successfully");
            echo json_encode(['status' => 'success', 'message' => 'Processed by Python']);
        } else {
            writeLog("❌ Python script failed");
            echo json_encode(['status' => 'error', 'message' => 'Python processing failed']);
        }
    } else {
        writeLog("ℹ️ Event $event ignored");
        echo json_encode(['status' => 'ignored', 'message' => 'Event not relevant']);
    }
    
} catch (Exception $e) {
    writeLog("❌ Exception: " . $e->getMessage());
    echo json_encode(['status' => 'error', 'message' => $e->getMessage()]);
}
?>