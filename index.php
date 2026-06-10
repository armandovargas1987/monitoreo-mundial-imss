<?php
declare(strict_types=1);

require_once __DIR__ . '/includes/config.php';

if (is_logged_in()) {
    header('Location: dashboard.php');
    exit;
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $usuario = trim($_POST['usuario'] ?? '');
    $clave = $_POST['clave'] ?? '';

    if ($usuario === DEMO_USER && $clave === DEMO_PASS) {
        $_SESSION['usuario'] = $usuario;
        $next = basename($_POST['next'] ?? 'dashboard.php');
        header('Location: dashboard.php');
        exit;
    }

    $error = 'Usuario o contraseña incorrectos.';
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Acceso · Monitoreo IMSS · Mundial 2026</title>
<link rel="stylesheet" href="assets/css/login.css">
</head>
<body>
<form class="card" method="post" autocomplete="off">
  <input type="hidden" name="next" value="dashboard.php">
  <div class="seal">IMSS</div>
  <h1><?= htmlspecialchars(APP_NAME) ?></h1>
  <div class="sub"><?= htmlspecialchars(APP_SUBTITLE) ?></div>
  <label>Usuario</label>
  <input name="usuario" placeholder="nombre.apellido" required autofocus>
  <label>Contraseña</label>
  <input name="clave" type="password" placeholder="••••••••" required>
  <?php if ($error): ?>
    <div class="err"><?= htmlspecialchars($error) ?></div>
  <?php endif; ?>
  <button type="submit">Ingresar</button>
  <div class="foot"><?= htmlspecialchars(APP_FOOTER) ?></div>
</form>
</body>
</html>
