<?php
declare(strict_types=1);

require_once __DIR__ . '/includes/config.php';
require_login();

$estadiosData = load_estadios_data();
$estadioMeta = estadio_meta();
$activeSede = $_GET['sede'] ?? 'Estadio Azteca';
if (!isset($estadioMeta[$activeSede])) {
    $activeSede = 'Estadio Azteca';
}

$umfs = $estadiosData[$activeSede] ?? [];
$meta = $estadioMeta[$activeSede];
$totalUmfs = count($umfs);
$conUrgencias = count(array_filter($umfs, fn($u) => ($u['urgencias'] ?? '0') !== '0'));
$conContinua = count(array_filter($umfs, fn($u) => ($u['atencion_continua'] ?? '0') !== '0'));
$distProm = $totalUmfs > 0
    ? round(array_sum(array_column($umfs, 'dist_km')) / $totalUmfs, 1)
    : 0;

$mapPayload = [
    'estadio' => [
        'nombre' => $activeSede,
        'lat' => $meta['lat'],
        'lon' => $meta['lon'],
    ],
    'umfs' => $umfs,
];
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Monitoreo · <?= htmlspecialchars($activeSede) ?> · Mundial 2026</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="assets/css/dashboard.css">
</head>
<body>
<header class="topbar">
  <div class="brand">
    <div class="seal">IMSS</div>
    <div>
      <strong><?= htmlspecialchars(APP_NAME) ?></strong>
      <span><?= htmlspecialchars(APP_SUBTITLE) ?></span>
    </div>
  </div>
  <div class="topbar-actions">
    <span class="user"><?= htmlspecialchars($_SESSION['usuario']) ?></span>
    <a class="btn-outline" href="logout.php">Salir</a>
  </div>
</header>

<nav class="sedes">
  <?php foreach ($estadioMeta as $nombre => $info): ?>
    <a class="sede-tab <?= $nombre === $activeSede ? 'active' : '' ?>"
       href="?sede=<?= urlencode($nombre) ?>">
      <span class="sede-name"><?= htmlspecialchars($nombre) ?></span>
      <span class="sede-city"><?= htmlspecialchars($info['ciudad']) ?></span>
    </a>
  <?php endforeach; ?>
</nav>

<main class="layout">
  <section class="panel stats">
    <h2><?= htmlspecialchars($activeSede) ?></h2>
    <p class="delegacion">Delegación IMSS: <?= htmlspecialchars($meta['delegacion']) ?></p>
    <div class="kpi-grid">
      <article class="kpi">
        <span class="kpi-val"><?= $totalUmfs ?></span>
        <span class="kpi-label">UMF ≤ 10 km</span>
      </article>
      <article class="kpi">
        <span class="kpi-val"><?= $distProm ?> km</span>
        <span class="kpi-label">Distancia promedio</span>
      </article>
      <article class="kpi">
        <span class="kpi-val"><?= $conContinua ?></span>
        <span class="kpi-label">Atención continua</span>
      </article>
      <article class="kpi">
        <span class="kpi-val"><?= number_format($meta['capacidad']) ?></span>
        <span class="kpi-label">Capacidad estadio</span>
      </article>
    </div>
    <div class="fuente">
      <strong>Fuente cruzada:</strong>
      Sistema de Regionalización IMSS
      (<a href="<?= REGIONALIZACION_BASE ?>/aplicacion/controladores/inicio.php" target="_blank" rel="noopener">diagramas</a>)
      · CUUMSP Feb 2026
    </div>
  </section>

  <section class="panel map-panel">
    <div id="map"></div>
    <div class="map-legend">
      <span><i class="dot estadio"></i> Estadio</span>
      <span><i class="dot umf"></i> UMF cercana</span>
      <span><i class="dot radio"></i> Radio 10 km</span>
    </div>
  </section>

  <section class="panel table-panel">
    <div class="panel-head">
      <h3>UMF cercanas al estadio</h3>
      <span class="badge"><?= $totalUmfs ?> unidades</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Unidad</th>
            <th>Delegación</th>
            <th>Dist. estadio</th>
            <th>Hospital refiere</th>
            <th>Dist. hospital</th>
            <th>Cons. MF</th>
            <th>PAMF</th>
            <th>Servicios</th>
          </tr>
        </thead>
        <tbody>
          <?php if ($totalUmfs === 0): ?>
            <tr><td colspan="9" class="empty">Sin unidades en el radio configurado.</td></tr>
          <?php endif; ?>
          <?php foreach ($umfs as $i => $umf): ?>
            <tr data-lat="<?= htmlspecialchars((string)$umf['lat']) ?>"
                data-lon="<?= htmlspecialchars((string)$umf['lon']) ?>">
              <td><?= $i + 1 ?></td>
              <td>
                <strong><?= htmlspecialchars($umf['nombre']) ?></strong>
                <small><?= htmlspecialchars($umf['cve'] ?? '') ?></small>
              </td>
              <td><?= htmlspecialchars($umf['delegacion']) ?></td>
              <td><span class="pill"><?= htmlspecialchars((string)$umf['dist_km']) ?> km</span></td>
              <td><?= htmlspecialchars($umf['hospital'] ?: '—') ?></td>
              <td><?= htmlspecialchars($umf['dist_hosp'] ?: '—') ?></td>
              <td><?= htmlspecialchars($umf['cons_mf'] ?: '—') ?></td>
              <td><?= htmlspecialchars($umf['pamf'] ?: '—') ?></td>
              <td>
                <?php if (($umf['atencion_continua'] ?? '0') !== '0'): ?>
                  <span class="tag tag-green">Continua</span>
                <?php endif; ?>
                <?php if (($umf['urgencias'] ?? '0') !== '0'): ?>
                  <span class="tag tag-red">Urgencias</span>
                <?php endif; ?>
              </td>
            </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    </div>
  </section>

  <section class="panel alert-panel">
    <div class="panel-head">
      <h3>Monitoreo de entorno · Zona sede</h3>
      <span class="live">● En línea</span>
    </div>
    <div class="alert-grid">
      <article class="alert-card nivel-bajo">
        <h4>Rutas de acceso</h4>
        <p>UMF más cercana: <strong><?= htmlspecialchars($umfs[0]['nombre'] ?? 'N/D') ?></strong>
          (<?= htmlspecialchars((string)($umfs[0]['dist_km'] ?? '—')) ?> km)</p>
      </article>
      <article class="alert-card nivel-medio">
        <h4>Capacidad instalada</h4>
        <p><?= array_sum(array_map('intval', array_column($umfs, 'cons_mf'))) ?> consultorios MF
          en radio de 10 km alrededor del estadio.</p>
      </article>
      <article class="alert-card nivel-info">
        <h4>Regionalización</h4>
        <p>Datos sincronizados desde catálogos delegacionales
          (<?= htmlspecialchars($meta['delegacion']) ?>).</p>
      </article>
    </div>
  </section>
</main>

<footer class="footer">
  <?= htmlspecialchars(APP_FOOTER) ?> ·
  Usuario: <?= htmlspecialchars($_SESSION['usuario']) ?> ·
  Actualizado: <?= date('d/m/Y H:i') ?>
</footer>

<script>
window.MONITOREO_DATA = <?= json_encode($mapPayload, JSON_UNESCAPED_UNICODE) ?>;
</script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="assets/js/dashboard.js"></script>
</body>
</html>
