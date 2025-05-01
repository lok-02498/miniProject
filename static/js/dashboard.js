document.addEventListener('DOMContentLoaded', function() {
    const lowStockList = document.getElementById('low-stock-list');
    const expiringSoonList = document.getElementById('expiring-soon-list');

    function fetchNotifications() {
        fetch('/notifications')
            .then(response => response.json())
            .then(data => {
                updateNotifications(data);
            })
            .catch(error => {
                console.error('Error fetching notifications:', error);
            });
    }

    function updateNotifications(notifications) {
        // Update Low Stock Items
        lowStockList.innerHTML = ''; // Clear the current list
        if (notifications.low_stock && notifications.low_stock.length > 0) {
            notifications.low_stock.forEach(item => { // Loop through ALL low stock items
                const li = document.createElement('li');
                li.className = 'notification-item';
                li.innerHTML = `
                    <span class="product-name">${item.Product}</span>
                    <span class="stock-level">Stock: <span class="low-stock">${item.Stock}</span></span>
                `;
                lowStockList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.className = 'notification-item';
            li.textContent = 'No low stock items.';
            lowStockList.appendChild(li);
        }

        // Update Expiring Soon Items
        expiringSoonList.innerHTML = ''; // Clear the current list
        if (notifications.expiring_soon && notifications.expiring_soon.length > 0) {
            notifications.expiring_soon.forEach(item => { // Loop through ALL expiring soon items
                const li = document.createElement('li');
                li.className = 'notification-item';
                li.innerHTML = `
                    <span class="product-name">${item.Product}</span>
                    <span class="expiry-date">Expires: <span class="expiring-soon">${item['Expiration Date']}</span></span>
                `;
                expiringSoonList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.className = 'notification-item';
            li.textContent = 'No items expiring soon.';
            expiringSoonList.appendChild(li);
        }
    }

    // Fetch notifications on page load
    fetchNotifications();

    // Poll for new notifications periodically
    setInterval(fetchNotifications, 5000);
});