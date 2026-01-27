# API - Endpoints para móviles

Resumen rápido:
- Base API: `/dashboard/api/` (las rutas están registradas bajo el namespace `properties` en `properties/urls.py`).

Endpoints principales:
- `GET /dashboard/api/properties/` — Lista paginada de propiedades activas.
  - Parámetros de consulta útiles:
    - `page` — número de página (paginación por `PageNumberPagination`, 20 por página por defecto).
    - filtros por campo (query params): `province`, `district`, `property_type`, `status`, `currency`.
    - búsqueda: `search` (buscar en `title`, `description`, `address`).
    - orden: `ordering` (ej.: `?ordering=-price` o `?ordering=created_at`).

- `GET /dashboard/api/properties/{id}/` — Detalle de una propiedad (anida imágenes, videos, documentos, rooms, owner, financial_info).

Autenticación:
- Se usa JWT para clientes móviles. Endpoints:
  - `POST /api/token/` — obtener `access` y `refresh` tokens. En el body enviar JSON: `{"username": "...", "password": "..."}`.
  - `POST /api/token/refresh/` — renovar token `access` con `refresh`.

Uso (ejemplo con Retrofit/OkHttp):
- Llamar a `POST /api/token/` para obtener `access`.
- En solicitudes a `/dashboard/api/properties/` incluir cabecera: `Authorization: Bearer <access>`.

Notas de implementación:
- Los serializadores usan `request` para construir URLs absolutas de media (imágenes, videos, documentos).
- Filtros implementados con `django-filter` y `SearchFilter`/`OrderingFilter`.
- Paginación por número de página, `PAGE_SIZE = 20`.

Próximos pasos recomendados:
- Añadir scopes/permission más restrictivos para endpoints de escritura.
- Limitar campos sensibles en el serializer público si es necesario.

Contacto:
- Equipo backend: repositorio en branch `feature/nueva-funcionalidad`.
