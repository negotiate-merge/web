// Confirm registration password conforms to strength requirements
let password = document.getElementById('password');
let confirmation = document.getElementById('confirmation')
let register = document.getElementById('register')

// Regex confirmation criteria
let passwordConforms = new RegExp('(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^A-Za-z0-9])(?=.{8,})')
// Checks for 8 lowercase chars
//let passwordConforms = new RegExp('(?=.*[a-z])(?=.{8,})')


// Checks if password conforms to RegExp
function is_valid(passwordParam) {
    if (passwordConforms.test(passwordParam)) {
        register.disabled = false;
    }
}

// Timeout before a callback is called
let timeout;

// Add event listener to the password input field
password.addEventListener('input', () => {
    clearTimeout(timeout)
    
    // Call is_valid as a callback
    timeout = setTimeout(() => is_valid(password.value), 500)

    // Disables button if input field changes
    if (!is_valid(password.value)) {
        register.disabled = true;
    }
});
