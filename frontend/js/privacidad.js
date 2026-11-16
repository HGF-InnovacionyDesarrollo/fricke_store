"use strict";
pintarIconos();
cargarConfig().then((c) => { document.title = `Política de privacidad · ${c.producto}`; });
