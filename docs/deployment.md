# Deployment and troubleshooting

## Deployment

Deployment is a build step followed by static collection and application release.
The repository does not yet choose a hosting platform or production server.
Local static integration and collection are configured; production server and
settings configuration still need to be supplied for this procedure.

1. Install Python dependencies in the deployment environment and configure the
   production settings. Set `DEBUG=False`, appropriate `ALLOWED_HOSTS`, and a
   production secret key supplied outside source control. Configure persistent
   database/upload storage and HTTPS for the chosen host. Export
   `DJANGO_SETTINGS_MODULE` with the actual production settings module before
   running management commands; no production settings module is supplied yet.
2. Build from the release's lockfile on the build machine:

   ```bash
   cd frontend
   npm ci
   npm run build
   cd ..
   ```

3. From the root, using production settings and the Python environment, validate
   the release, apply its migrations, then collect its built assets:

   ```bash
   python manage.py check --deploy
   python manage.py test
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

   Resolve deployment-check warnings for the actual environment. `collectstatic`
   requires `STATIC_ROOT`; it does not build the frontend. Confirm that the
   collected directory contains `dist/main.js`, `dist/main.css`, and any referenced
   `dist/assets/` files.

4. Publish the complete collected static directory through the host's static
   server or configured static storage backend at `STATIC_URL`. Run Django through
   a production WSGI/ASGI server using `bookEx.wsgi:application` or
   `bookEx.asgi:application`. Choose and install a server supported by the host;
   Django's development `runserver` is not the production server.
5. Release application code and matching assets together, then check login,
   books, and messaging under production settings. Verify JS/CSS MIME types,
   module loading, fonts/images, and static requests from nested routes. Review
   browser console/network errors. Node and `node_modules` may stay on the build
   machine; deploy the Python application and collected assets.

The current upload implementation writes book images into
`bookEx/static/uploads/`. Preserve those files across releases and verify new
uploads remain visible under the production serving arrangement: a one-time
static collection does not publish subsequent uploads automatically. Persistent
upload serving needs to be resolved before deployment; the frontend build must
never delete uploaded files.

### Cache invalidation

`main.js` and `main.css` have stable filenames. Configure those URLs for cache
revalidation (for example, `Cache-Control: no-cache` with ETag/Last-Modified) and
purge any CDN copies on release. Avoid immutable caching of these entry files.
Hashed files under `dist/assets/` may use long-lived immutable caching; retain
previously referenced hashed assets while cached pages/bundles can still use them.
Publish each release as a matching set of code and static files and retain a
matching set for rollback. A manifest-based static backend is a separate change
that needs validation against emitted CSS/JS asset references.

### Troubleshooting

| Symptom | Check |
| --- | --- |
| Bundler cannot resolve `src/main.css` | The stylesheet must match the path in `build.mjs`; the current name is `main.css` |
| `tsc` or esbuild is missing | Run `npm ci` in `frontend/` with development dependencies included |
| Styles look unchanged | Rebuild, confirm `prototype.css` is imported, and inspect `/static/dist/main.css` |
| Build succeeds but the page looks unchanged | Load bundles in `base.html`, refresh, and inspect the network panel |
| Nested routes return asset 404s | Use Django static tags and verify the static URL/server mapping |
| `collectstatic` reports no filesystem path | Configure `STATIC_ROOT` in the settings used for that command |
| Watch output exists despite type errors | Bundle watch and typecheck watch are separate; production build checks types first |

See Django's [static deployment guide](https://docs.djangoproject.com/en/6.0/howto/static-files/deployment/)
and [deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)
for the collection/serving boundary and production settings requirements.
