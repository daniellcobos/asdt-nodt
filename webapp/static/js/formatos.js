    function fnt_sino(valor){
      t = '';
        if (valor == 0) { t = 'No'};
        if (valor == 1) { t = 'Si'};
      return t
    }

    function fnt_sino_texto(valor) {
      t = fnt_sino(valor);
      document.write(t);
    }


    function fnt_format_procentaje(valor, decimales){
      return (valor * 100).toFixed(decimales) + '%'
    }
    function fnt_tmes(mes){
        t = '';
        //console.log(mes);
        if (mes == 1) { t = 'Enero'};
        if (mes == 2) { t = 'Febrero'};
        if (mes == 3) { t = 'Marzo'};
        if (mes == 4) { t = 'Abril'};
        if (mes == 5) { t = 'Mayo'};
        if (mes == 6) { t = 'Junio'};
        if (mes == 7) { t = 'Julio'};
        if (mes == 8) { t = 'Agosto'};
        if (mes == 9) { t = 'Septiembre'};
        if (mes == 10) { t = 'Octubre'};
        if (mes == 11) { t = 'Noviembre'};
        if (mes == 12) { t = 'Diciembre'};
      return t
    }
    function fnt_perfil(p){
        t = '';
        if (p == -2) { t = 'Superadmin'};
        if (p == -1) { t = 'Admin de país'};
        if (p == 1) { t = 'Consultor'};
        if (p == 10) { t = 'Gerente de Ventas'};
        if (p == 11) { t = 'Director'};
        if (p == 12) { t = 'Finanzas'};

      return t
    }    
    function fnt_aprobado(valor){
      t = '';
        if (valor == 0) { t = 'ND'};
        if (valor == 1) { t = 'Si'};
        if (valor == 2) { t = 'No'};
        if (valor == 3) { t = 'Cancelado'};        
      return t
    }

    function fnt_aprobado_texto(valor) {
      t = fnt_aprobado(valor);
      document.write(t);
    }
