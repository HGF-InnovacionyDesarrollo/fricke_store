"use strict";
pintarIconos();
cargarConfig().then((c) => { document.title = `Aviso de privacidad · ${c.producto}`; });
