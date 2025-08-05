document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('deliveryreport_form');
    if (form) {
        // Create loader container
        const loaderWrapper = document.createElement('div');
        loaderWrapper.style.position = 'fixed';
        loaderWrapper.style.top = '0';
        loaderWrapper.style.left = '0';
        loaderWrapper.style.width = '100%';
        loaderWrapper.style.height = '100%';
        loaderWrapper.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        loaderWrapper.style.display = 'flex';
        loaderWrapper.style.flexDirection = 'column';
        loaderWrapper.style.alignItems = 'center';
        loaderWrapper.style.justifyContent = 'center';
        loaderWrapper.style.zIndex = '9999';
        loaderWrapper.style.fontFamily = 'sans-serif';
        loaderWrapper.style.fontSize = '16px';

        // Create spinner
        const spinner = document.createElement('div');
        spinner.style.border = '6px solid #f3f3f3';
        spinner.style.borderTop = '6px solid #3498db';
        spinner.style.borderRadius = '50%';
        spinner.style.width = '60px';
        spinner.style.height = '60px';
        spinner.style.animation = 'spin 1s linear infinite';

        // Create message
        const message = document.createElement('p');
        message.textContent = 'Regenerating report documents. It may take some time.';
        message.style.marginTop = '20px';
        message.style.color = '#333';

        // Append spinner and message to wrapper
        loaderWrapper.appendChild(spinner);
        loaderWrapper.appendChild(message);

        // Spinner animation
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);

        // Show loader on submit
        form.addEventListener('submit', function () {
            document.body.appendChild(loaderWrapper);
        });
    }
});
