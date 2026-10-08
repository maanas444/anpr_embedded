
<?php
/**
 * receiver.php
 * ------------
 * Receives data via HTTP GET parameters (sent by sender.py), sanitizes
 * it, and calls receiver.py passing the data as command line arguments.
 *
 * Expected parameters:
 * number_plate - e.g. EAG942
 * camera - e.g. 12
 *
 * Example request:
 * http://<pi-ip>/receiver.php?number_plate=EAG942&camera=12
 */
header('Content-Type: text/plain');

if (isset($_GET['node_id']) && isset($_GET['number_plate']) && isset($_GET['timestamp_ns'])) {
    $nodeID = $_GET['node_id'];
    $licensePlate = $_GET['number_plate'];
    $timestamp = $_GET['timestamp_ns'];
    // Sanitize input before passing it to the shell.
    // escapeshellarg() wraps each value in quotes and escapes any
    // special characters (including spaces), so the value is treated
    // as a single, safe argument and cannot be used to inject extra
    // shell commands.
    $safeLicensePlate = escapeshellarg($licensePlate);
    $safeNodeID = escapeshellarg($nodeID);
    $safeTimestamp = escapeshellarg($timestamp);
    
    // Call the receiver python script, passing the sanitized values
    // as command line arguments (argv[1] and argv[2]).
    $command = "/var/www/venv/python3 " . __DIR__ . "/database/db_manager.py write " . $safeNodeID . " " . $safeLicensePlate . " " . $safeTimestamp;
    $output = shell_exec($command);
    
    echo "Data forwarded to receiver script.\n";
    echo $output;

} else {
    http_response_code(400);
    echo "Missing parameters. Expected: node_id, number_plate and timestamp_ns.\n";
}
?>