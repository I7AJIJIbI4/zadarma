<?php
header('Content-Type: text/html; charset=utf-8');
echo "<!DOCTYPE html><html><head><meta charset='utf-8'><title>🧪 Webhook Test</title></head><body>";
echo "<h1>🧪 Zadarma Webhook Test</h1>";

$webhook_url = 'https://gomonclinic.com/zadarma_ivr_webhook.php';

// Тест 1: Zadarma validation
echo "<h2>1. ✅ Zadarma Validation:</h2>";
$result = @file_get_contents($webhook_url . '?zd_echo=test123');
echo "Результат: <strong>" . ($result === 'test123' ? '✅ OK' : '❌ FAIL') . "</strong><br>";

// Тест 2: Status
echo "<h2>2. 📊 Status:</h2>";
$status = @file_get_contents($webhook_url);
echo "<pre>$status</pre>";

// Тест 3: POST тест
echo "<h2>3. 📞 POST Test (NOTIFY_INTERNAL 103 - SMS):</h2>";
$data = [
    'event' => 'NOTIFY_INTERNAL',
    'caller_id' => '380933297777',
    'internal' => '103',
    'call_start' => date('Y-m-d H:i:s')
];

$context = stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => json_encode($data)
    ]
]);

$result = @file_get_contents($webhook_url, false, $context);
echo "SMS тригер результат: <pre>$result</pre>";

echo "<h2>📝 Логи:</h2>";
$log_file = '/home/gomoncli/zadarma/ivr_webhook.log';
if (file_exists($log_file)) {
    $logs = file_get_contents($log_file);
    $lines = explode("\n", trim($logs));
    $last_lines = array_slice($lines, -20);
    echo "<pre style='background:#f5f5f5;padding:10px;'>" . implode("\n", $last_lines) . "</pre>";
} else {
    echo "<p>❌ Лог файл не знайдено</p>";
}

echo "<h2>🔗 Посилання:</h2>";
echo "<ul>";
echo "<li><a href='$webhook_url'>📊 Webhook Status</a></li>";
echo "<li><strong>URL для Zadarma:</strong> <code>$webhook_url</code></li>";
echo "</ul>";

echo "</body></html>";
?>
