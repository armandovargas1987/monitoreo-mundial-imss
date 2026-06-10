# Publicar el monitor en internet (siempre activo)

No necesitas GitHub. Con **Netlify** (gratis) el monitor queda en línea 24/7 aunque apagues tu Mac.

## Paso 1 — Crear cuenta (una sola vez, ~2 min)

1. Abre **https://www.netlify.com/**
2. Clic en **Sign up**
3. Regístrate con **Google** o correo (es gratis)

## Paso 2 — Subir el sitio

1. En Netlify, clic en **Add new site** → **Deploy manually**
2. Arrastra el archivo **`monitoreo-imss-mundial2026.zip`** desde tu carpeta Descargas  
   (o vuelve a generarlo con `./scripts/crear-paquete.sh`)
3. Espera ~30 segundos a que termine el despliegue

## Paso 3 — Liga para tus jefes

Netlify te dará una URL como:

`https://nombre-random-123.netlify.app`

**Liga del monitor (mándala así):**

`https://TU-URL.netlify.app/monitor.html`

También funciona la raíz (`/`) — redirige al monitor automáticamente.

## Paso 4 — Nombre más bonito (opcional)

En Netlify: **Site configuration** → **Domain management** → **Options** → **Edit site name**

Ejemplo: `monitoreo-imss-mundial2026.netlify.app`

Quedaría:

`https://monitoreo-imss-mundial2026.netlify.app/monitor.html`

## Actualizar datos después

Si cambias marchas, noticias o el mapa:

1. Corre `./scripts/crear-paquete.sh` en la carpeta del proyecto
2. En Netlify: **Deploys** → arrastra el zip nuevo (reemplaza el sitio)

## Administración

- **Monitor público:** `/monitor.html` (sin login)
- **Panel de captura:** `/acceso.html` → usuario `marvin.ortiz` / clave `DH2026!`
