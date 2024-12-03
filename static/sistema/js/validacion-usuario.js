$(document).ready(function () {
    $('#mensaje_error').hide()
    $('#mensaje_error_usu').hide()
    $('#mensaje_error_correo').hide()
    $('#mensaje_error_input').hide()
    $('#passstrength').hide()
    $('#mensaje_error_input_a').hide()
  
    // Hacer algo si el checkbox ha sido seleccionado
  
    $('#usuario').show()
    $('#contra').show()
    $('#contra1').show()
    $('#usuario').attr('required', true)
    $('#contra').attr('required', true)
    $('#contra1').attr('required', true)
    var cambioDePass = function () {
      var cont = $('#contra').val()
      var cont2 = $('#contra1').val()
      if (cont == '') {
        $('#mensaje_error').hide()
        $('#passstrength').hide()
      } else if (cont == cont2) {
        $('#mensaje_error').hide()
        $('#mensaje_error').attr('class', 'control-label col-md-12 text-success')
        $('#mensaje_error').show()
        $('#passstrength').show()
        $('#mensaje_error').html('Las constraseñas si coinciden')
        var strongRegex = new RegExp(
          '^(?=.{8,})(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*\\W).*$',
          'g',
        )
        var mediumRegex = new RegExp(
          '^(?=.{7,})(((?=.*[A-Z])(?=.*[a-z]))|((?=.*[A-Z])(?=.*[0-9]))|((?=.*[a-z])(?=.*[0-9]))).*$',
          'g',
        )
        var enoughRegex = new RegExp('(?=.{6,}).*', 'g')
        if (false == enoughRegex.test(cont)) {
          $('#passstrength').html('Más caracteres.')
        } else if (strongRegex.test(cont)) {
          $('#passstrength').className = 'ok'
          $('#passstrength').attr('class', 'control-label col-md-12 text-success')
          $('#passstrength').html(' Contraseña es fuerte!')
          $('#passstrength').show()
          $('#boton-enviar').removeAttr('disabled')
        } else if (mediumRegex.test(cont)) {
          $('#passstrength').className = 'alert'
          $('#passstrength').attr('class', 'control-label col-md-12 text-warning')
          $('#passstrength').html('Contraseña es media!')
          $('#passstrength').show()
        } else {
          $('#passstrength').className = 'error'
          $('#passstrength').show()
          $('#passstrength').attr('class', 'control-label col-md-12 text-danger')
          $('#passstrength').html('Contraseña es débil!')
        }
        // $('#boton-enviar').removeAttr("disabled");
      } else {
        $('#mensaje_error').html('Las constraseñas no coinciden')
        $('#mensaje_error').attr('class', 'control-label col-md-12 text-danger')
        $('#mensaje_error').show()
      }
    }
  
    $('#contra').on('keyup', cambioDePass)
    $('#contra1').on('keyup', cambioDePass)
  
    var cambioDeus = function () {
      var usuario = $('#loginUser').val()
      alert("a")
  
      $.ajax({
        url: '/buscarUsuarioNuevo',
        type: 'POST',
        data: {
          usuario: usuario,
        },
        success: function (response) {
          if (response == 'no existe') {
            $('#mensaje_error_usu').hide()
            $('#mensaje_error_usu').attr(
              'class',
              'control-label col-md-12 text-success',
            )
            $('#mensaje_error_usu').show()
            $('#mensaje_error_usu').html('Usuario Válido')
            $('#boton-enviar').removeAttr('disabled')
          } else {
            $('#mensaje_error_usu').html('El usuario ya existe')
            $('#mensaje_error_usu').attr(
              'class',
              'control-label col-md-12 text-danger',
            )
            $('#mensaje_error_usu').show()
            if (usuario == '') {
              $('#mensaje_error_usu').hide()
            }
          }
        },
        error: function (error) {
          //console.log(error);
        },
      })
    }
  
    $('#loginUser').on('keyup', cambioDeus)
  
  
    document.getElementById('nombre').addEventListener('input', (e) => {
      let value = e.target.value
      e.target.value = value.replace(/[^a-z-A-Z- -]/, '')
      var nombre = $('#nombre').val()
      var resu = validarnombre(nombre)
  
      if (resu == 1) {
        $('#mensaje_error_input').html('El nombre esta vacio')
        $('#mensaje_error_input').attr(
          'class',
          'control-label col-md-12 text-danger',
        )
        $('#mensaje_error_input').show()
      } else if (resu == 2) {
        $('#mensaje_error_input').html(
          'El nombre deb tener al menos 3 caracteres',
        )
        $('#mensaje_error_input').attr(
          'class',
          'control-label col-md-12 text-danger',
        )
        $('#mensaje_error_input').show()
      } else if (resu == 3) {
        $('#mensaje_error_input').html('El nombre no debe tener caracteres raros')
        $('#mensaje_error_input').attr(
          'class',
          'control-label col-md-12 text-danger',
        )
        $('#mensaje_error_input').show()
      } else {
        $('#mensaje_error_input').hide()
        $('#boton-enviar').removeAttr('disabled')
      }
    })
  })
  
  function añadir() {
    $.ajax({
      url: '/nuevou',
      type: 'POST',
      data: {
        nombres: $('#nombre').val(),
        apellidos: $('#apellido').val(),
        correo: $('#correo').val(),
        telefono: $('#telfijo').val(),
        celular: $('#celular').val(),
        direccion: $('#direccion').val(),
        loginUser: $('#usuario').val(),
        loginPassword: $('#contra').val(),
        rol: $('#rol').val(),
        flag: '',
      },
      success: function (response) {
        $.ajax({
          url: '/correo',
          type: 'POST',
          data: {
            nombres: $('#nombre').val(),
            apellidos: $('#apellido').val(),
            correo: $('#correo').val(),
            loginUser: $('#usuario').val(),
            loginPassword: $('#contra').val(),
          },
          success: function (response) {
            Swal.fire({
              title: 'Usuario Registrado Correctamente!',
              text:
                'Se envio un correo con las credenciales al ' +
                $('#correo').val(),
              icon: 'success',
              confirmButtonText: 'Aceptar',
            }).then(() => {
              window.location = '/'
            })
          },
          error: function (error) {
            //console.log(error);
          },
        })
      },
      error: function (error) {
        //console.log(error);
      },
    })
  }