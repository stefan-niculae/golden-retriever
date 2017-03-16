$('form').submit (e) ->
  window.location.pathname = $('input').val()
  e.preventDefault()
  false

$('.see-more').click (e) ->
  button = $(e.target)
  extraElements = button.parent('.body').find('.extra')
  console.log extraElements.eq(0)

  if extraElements.eq(0).is(':visible')
    button.text 'See all'
  else
    button.text 'See less'

  extraElements.toggle()


$(document).keydown (e) ->
  char = String.fromCharCode e.keyCode
  if /[a-z0-9]/i.test char  # alphanumeric
    $('input').focus()
