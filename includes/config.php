<?php
declare(strict_types=1);

session_start();

define('APP_NAME', 'Centro de Monitoreo');
define('APP_SUBTITLE', 'Marchas y Manifestaciones · Mundial 2026');
define('APP_FOOTER', 'CVOED–CPES · Acceso restringido');

define('DEMO_USER', 'marvin.ortiz');
define('DEMO_PASS', 'DH2026!');

define('DATA_FILE', __DIR__ . '/../data/estadios_umf.json');
define('REGIONALIZACION_BASE', 'http://11.22.41.200/region');

function is_logged_in(): bool
{
    return !empty($_SESSION['usuario']);
}

function require_login(): void
{
    if (!is_logged_in()) {
        header('Location: index.php');
        exit;
    }
}

function load_estadios_data(): array
{
    if (!file_exists(DATA_FILE)) {
        return [];
    }

    $json = file_get_contents(DATA_FILE);
    $data = json_decode($json ?: '[]', true);

    return is_array($data) ? $data : [];
}

function estadio_meta(): array
{
    return [
        'Estadio Azteca' => [
            'ciudad' => 'Ciudad de México',
            'delegacion' => 'CD México Sur',
            'lat' => 19.3029,
            'lon' => -99.1506,
            'partidos' => 5,
            'capacidad' => 87523,
        ],
        'Estadio Akron' => [
            'ciudad' => 'Guadalajara, Jal.',
            'delegacion' => 'Jalisco',
            'lat' => 20.6819,
            'lon' => -103.4616,
            'partidos' => 4,
            'capacidad' => 49850,
        ],
        'Estadio BBVA' => [
            'ciudad' => 'Monterrey, N.L.',
            'delegacion' => 'Nuevo León',
            'lat' => 25.6866,
            'lon' => -100.2451,
            'partidos' => 4,
            'capacidad' => 53500,
        ],
    ];
}
