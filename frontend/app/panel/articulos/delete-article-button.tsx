'use client';

import { Button } from '@mmanto/devbout-ui';

/** Boton de baja: confirma antes de disparar la Server Action del form padre. */
export function DeleteArticleButton() {
  return (
    <Button
      type="submit"
      variant="destructive"
      onClick={(event) => {
        if (!window.confirm('¿Borrar este artículo?')) event.preventDefault();
      }}
    >
      Borrar artículo
    </Button>
  );
}
