$('#login-form').submit(function (e) {
  e.preventDefault(); // Prevent the default form submission behavior

  const loginData = {
      till_number: $('#till_number').val(),
      operator_name: $('#operator_name').val(),
      password: $('#password').val(),
  };

  $.ajax({
      url: '/login',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(loginData),
      success: function (response) {
          if (response.success) {
              // Redirect to the allocate points page
              window.location.href = response.redirect; // Redirect user explicitly
          } else {
              // Display error message
              $('#error-message').show().text('Invalid credentials. Please try again.');
          }
      },
      error: function () {
          $('#error-message').show().text('An error occurred. Please try again.');
      },
  });
});
