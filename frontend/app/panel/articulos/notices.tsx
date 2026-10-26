/**
 * El modulo `articles` esta apagado en este club: la API responde 404 y el panel no
 * tiene nada que gestionar. Es un estado esperado, no un error.
 */
export function ModuloApagado() {
  return (
    <>
      <div className="flex flex-col gap-1">
        <h1 className="font-heading heading-screen font-medium">Artículos</h1>
        <p className="text-sm text-muted-foreground">Panel del portal</p>
      </div>
      <div className="rounded-xl border border-dashed p-8 text-center">
        <p className="text-sm font-medium">Módulo de artículos apagado</p>
        <p className="mx-auto mt-1 max-w-md text-xs text-muted-foreground">
          El módulo no está habilitado en este portal. Un admin de plataforma puede encenderlo
          desde la ficha del portal.
        </p>
      </div>
    </>
  );
}
