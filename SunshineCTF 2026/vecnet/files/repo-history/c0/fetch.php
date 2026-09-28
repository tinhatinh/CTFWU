<?php
declare(strict_types=1);

// Players must recover this exact internal URL from the site's Git history.
// It remains a clue, but it is never used as an outbound request target.
const ALLOWED_URL = 'http://localhost/files/specs.7z';
const ARCHIVE_PATH = '/var/www/html/files/specs.7z';
const MAX_ARCHIVE_BYTES = 1048576;

function fail_request(int $status, string $message): never {
    http_response_code($status);
    header('Content-Type: text/plain; charset=utf-8');
    header('X-Content-Type-Options: nosniff');
    echo $message;
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'GET') {
    header('Allow: GET');
    fail_request(405, 'method not allowed');
}

if (!isset($_GET['url']) || !is_string($_GET['url']) || !hash_equals(ALLOWED_URL, $_GET['url'])) {
    fail_request(403, 'endpoint not allowed');
}

$size = @filesize(ARCHIVE_PATH);
if ($size === false || $size > MAX_ARCHIVE_BYTES || !is_file(ARCHIVE_PATH) || !is_readable(ARCHIVE_PATH)) {
    fail_request(500, 'archive unavailable');
}

header('Content-Type: application/x-7z-compressed');
header('Content-Disposition: attachment; filename="specs.7z"');
header('Content-Length: ' . (string) $size);
header('X-Content-Type-Options: nosniff');

if (readfile(ARCHIVE_PATH) === false) {
    fail_request(500, 'archive unavailable');
}
