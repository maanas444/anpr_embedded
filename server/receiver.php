
<?php
/**
 * receiver.php
 * ------------
 * Receives data via HTTP GET parameters (sent by sender.py), sanitizes
 * it, and calls receiver.py passing the data as command line arguments.
 *
 * Expected parameters:
 * license_plate - e.g. EAG942
 * camera - e.g. 12
 *
 * Example request:
 * http://<pi-ip>/receiver.php?license_plate=EAG942&camera=12
 */
header('Content-Type: text/plain');

if (isset($_GET['license_plate']) && isset($_GET['camera'])) {
    $licensePlate = $_GET['license_plate'];
    $camera = $_GET['camera'];
    // Sanitize input before passing it to the shell.
    // escapeshellarg() wraps each value in quotes and escapes any
    // special characters (including spaces), so the value is treated
    // as a single, safe argument and cannot be used to inject extra
    // shell commands.
    $safeLicensePlate = escapeshellarg($licensePlate);
    $safeCamera = escapeshellarg($camera);
    
    // Call the receiver python script, passing the sanitized values
    // as command line arguments (argv[1] and argv[2]).
    $command = "python3 " . __DIR__ . "/receiver.py " . $safeLicensePlate . " " . $safeCamera;
    $output = shell_exec($command);
    
    echo "Data forwarded to receiver script.\n";
    echo $output;

} else {
    http_response_code(400);
    echo "Missing parameters. Expected: license_plate and camera.\n";
}
?>