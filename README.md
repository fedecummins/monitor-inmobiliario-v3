# 🏠 Monitor Inmobiliario — GBA Norte

Monitor automático de propiedades en venta en Vicente López, Florida, La Lucila y San Isidro.  
**Precio:** USD 250.000 – 350.000 · **Tipos:** Casas, PH, Terrenos, Galpones, Depósitos  
**Portales:** Zonaprop · Argenprop · MercadoLibre · Properati · Inmuebles24

---

## 🚀 Setup en 5 minutos

### 1. Crear el repositorio en GitHub

1. Andá a [github.com/new](https://github.com/new)
2. Nombre: `monitor-inmobiliario` (o el que quieras)
3. Marcá **Public** (necesario para GitHub Pages gratis)
4. Click **Create repository**

### 2. Subir los archivos

```bash
git clone https://github.com/TU_USUARIO/monitor-inmobiliario.git
cd monitor-inmobiliario

# Copiá todos los archivos de este proyecto aquí
# Luego:
git add .
git commit -m "🏠 Initial commit — Monitor Inmobiliario"
git push origin main
```

### 3. Activar GitHub Pages

1. En tu repo → **Settings** → **Pages**
2. Source: `Deploy from a branch`
3. Branch: `main` / `/ (root)`
4. Click **Save**
5. En ~2 minutos tu sitio va a estar en: `https://TU_USUARIO.github.io/monitor-inmobiliario/`

### 4. Activar el scraper automático

El scraper ya está configurado en `.github/workflows/daily.yml` para correr todos los días a las **8:00 AM hora Argentina**.

Para correrlo manualmente la primera vez:
1. Ir a tu repo → **Actions**
2. Click en "Daily Scraping — Monitor Inmobiliario"
3. Click **Run workflow** → **Run workflow**
4. Esperar ~5-10 minutos
5. Refrescar el sitio — ¡van a aparecer las propiedades!

---

## 📁 Estructura del proyecto

```
monitor-inmobiliario/
├── index.html                  # Sitio web frontend
├── data/
│   └── properties.json         # Datos scrapeados (se actualiza solo)
├── scripts/
│   └── scraper.py              # Scraper Python
├── .github/
│   └── workflows/
│       └── daily.yml           # GitHub Action diaria
└── README.md
```

---

## ⚙️ Personalización

### Cambiar zonas o precios

Editá estas variables en `scripts/scraper.py`:

```python
ZONES = ["vicente-lopez", "florida", "la-lucila", "san-isidro"]
PRICE_MIN = 250000
PRICE_MAX = 350000
```

### Cambiar el horario del scraper

Editá el cron en `.github/workflows/daily.yml`:

```yaml
- cron: "0 11 * * *"   # 11:00 UTC = 08:00 ART
```

### Agregar o quitar portales

Comentá o descomentá los scrapers en la función `main()` de `scraper.py`.

---

## 🛠️ Troubleshooting

**El scraper corrió pero no aparecen propiedades:**  
Los portales inmobiliarios cambian sus estructuras HTML frecuentemente. Revisá los logs en la tab **Actions** de GitHub y ajustá los selectores CSS en `scraper.py`.

**GitHub Actions no tiene permisos para hacer push:**  
Settings → Actions → General → Workflow permissions → Seleccionar "Read and write permissions"

**Error 429 (rate limit) de los portales:**  
Aumentá los tiempos en `sleep_random()` en el scraper.

---

## 📊 Qué muestra el sitio

- ✦ **Nuevas incorporaciones** del día
- ↕ **Cambios de precio** (subas y bajas)  
- ✕ **Dadas de baja** (posiblemente vendidas)
- ▤ **Todas las propiedades** con filtros por zona, tipo, búsqueda y ordenamiento
- 📊 **Termómetro del mercado** con distribución por tipo y precio promedio
- 💡 **USD/m²** calculado automáticamente cuando hay superficie disponible

---

## 📝 Notas legales

Este scraper es de uso personal. Revisá los Términos de Servicio de cada portal antes de usar. Incluye delays entre requests para no sobrecargar los servidores.
