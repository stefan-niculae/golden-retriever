$('form').submit (e) ->
  window.location.pathname = $('input').val()
  e.preventDefault()
  false