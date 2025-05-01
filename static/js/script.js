document.addEventListener("DOMContentLoaded", function () {
    fetch("/get-inventory")
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        // Validate and sanitize data (very important)
        const sanitizedData = data.map(item => {
          if (typeof item.Category !== 'string') {
            item.Category = item.Category === null ? "N/A" : "Unknown"; // or "" or null, server side fix is best
          }
          return item;
        });
  
        populateTable(sanitizedData);
        populateCategoryFilter(sanitizedData);
      })
      .catch(error => {
        console.error("Error fetching inventory:", error);
        alert("Failed to load inventory. Check the console for details.");
      });
  
    const searchInput = document.getElementById("search");
    searchInput.addEventListener("keyup", function (event) {
      const searchTerm = event.target.value.toLowerCase();
      filterTable(searchTerm);
    });
  
    const categoryFilter = document.getElementById("categoryFilter");
    categoryFilter.addEventListener("change", function () {
      const selectedCategory = categoryFilter.value;
      filterByCategory(selectedCategory);
    });
  
    const addItemBtn = document.getElementById("addItemBtn");
    addItemBtn.addEventListener("click", addNewRow);
  
    
  });
  
  function calculateDaysRemaining(expirationDate) {
    const today = new Date();
    const expiry = new Date(expirationDate);
    const timeDiff = expiry.getTime() - today.getTime();
    return Math.ceil(timeDiff / (1000 * 3600 * 24));
  }
  
  function applyExpirationColor(td, days) {
    if (days > 30) {
      td.style.backgroundColor = "lightgreen";
    } else if (days >= 7) {
      td.style.backgroundColor = "yellow";
    } else {
      td.style.backgroundColor = "red";
      td.style.color = "white";
    }
  }
  
  function populateTable(data) {
    const table = document.getElementById("inventoryTable");
    const headers = ["Product", "Category", "Price", "Stock", "Supplier"];
    const lowStockThreshold = 50;
    table.innerHTML = "";
  
    data.forEach(item => {
      const tr = table.insertRow();
      tr.dataset.rowId = item.id;
  
      headers.forEach(header => {
        const td = tr.insertCell();
        td.textContent = item[header];
      });
  
      const stock = parseInt(item.Stock);
      if (stock <= lowStockThreshold) {
        tr.classList.add("low-stock");
      }
  
      const actionTd = tr.insertCell();
      actionTd.innerHTML = `
          <button class="remove-button" onclick="removeRow(this)">Remove</button>
          <button class="edit-button" onclick="editRow(this)">Edit</button>
        `;
  
      const expirationDate = item["Expiration Date"];
      const expirationTd = tr.insertCell();
  
      if (expirationDate) {
        const daysRemaining = calculateDaysRemaining(expirationDate);
        expirationTd.textContent = expirationDate;
        applyExpirationColor(expirationTd, daysRemaining);
      } else {
        expirationTd.textContent = "N/A";
      }
    });
  }
  
  function populateCategoryFilter(data) {
    const categoryFilter = document.getElementById("categoryFilter");
    const categories = new Set();
    categoryFilter.innerHTML = '<option value="">All Categories</option>';
  
    data.forEach(item => categories.add(item.Category));
  
    categories.forEach(category => {
      const option = document.createElement("option");
      option.value = category;
      option.text = category;
      categoryFilter.appendChild(option);
    });
  }
  
  function filterTable(searchTerm) {
    const table = document.getElementById("inventoryTable");
    const rows = table.getElementsByTagName("tr");
  
    for (const row of rows) {
      const productNameCell = row.cells[0];
      if (productNameCell) {
        const productName = productNameCell.textContent.toLowerCase();
        row.style.display = productName.includes(searchTerm) ? "" : "none";
      }
    }
  }
  
  function filterByCategory(selectedCategory) {
    const table = document.getElementById("inventoryTable");
    const rows = table.getElementsByTagName("tr");
    const selectedCategoryLower = selectedCategory.trim().toLowerCase();
  
    for (const row of rows) {
      const categoryCell = row.cells[1];
      if (categoryCell) {
        const rowCategory = categoryCell.textContent.trim().toLowerCase();
        row.style.display = (selectedCategory === "" || selectedCategoryLower === "all categories" || rowCategory === selectedCategoryLower) ? "" : "none";
      }
    }
  }
  
  function removeRow(button) {
    const row = button.parentElement.parentElement;
    const rowId = row.dataset.rowId;
  
    fetch(`/delete-inventory/${rowId}`, {
      method: 'DELETE',
    })
      .then(response => {
        if (!response.ok) {
          return response.json().then(err => {
            throw new Error(err.message || "Failed to delete item"); 
          });
        }
        row.remove();
        alert("Item deleted successfully!"); 
      })
      .catch(error => {
        console.error("Error deleting item: ", error);
        alert("Error deleting item: " + error.message); 
      });
  }
  
  function addNewRow() {
    const table = document.getElementById("inventoryTable");
    const newRow = table.insertRow();
    newRow.dataset.isNew = true;
  
    const headers = ["Product", "Category", "Price", "Stock", "Supplier"];
    headers.forEach(header => {
      const cell = newRow.insertCell();
      cell.innerHTML = `<input type="text">`;
  
      const input = cell.querySelector('input');
      input.addEventListener('blur', () => validateField(input, header));
    });
    const expirationCell = newRow.insertCell();
    expirationCell.innerHTML = `<input type="date">`;
  
    const actionCell = newRow.insertCell();
    actionCell.innerHTML = `
        <button class="save-button" onclick="saveNewRow(this)">Save</button>
        <button class="cancel-button" onclick="cancelNewRow(this)">Cancel</button>
      `;
  }
  
  function validateField(input, header) {
    const value = input.value;
    if (header === "Price" || header === "Stock") {
      const numValue = Number(value);
      if (isNaN(numValue) || numValue < 0) {
        alert(`Invalid ${header}. Please enter a non-negative number.`);
        input.focus();
        return false;
      }
    }
    return true;
  }
  
  function saveNewRow(button) {
    const row = button.parentElement.parentElement;
    const itemData = {};
    const headers = ["Product", "Category", "Price", "Stock", "Supplier"];
    let isValid = true;
  
    for (let i = 0; i < headers.length; i++) {
      const cell = row.cells[i];
      const input = cell.querySelector('input');
      if (!validateField(input, headers[i])) {
        isValid = false;
        break;
      }
      itemData[headers[i]] = input.value;
    }
    itemData["Expiration Date"] = row.cells[headers.length].querySelector('input').value;
  
    if (!isValid) return;
  
    fetch('/save-inventory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(itemData),
    })
      .then(response => {
        if (!response.ok) {
          return response.json().then(err => {
            throw new Error(err.message || "Failed to save new item.");
          });
        }
        return response.json();
      })
      .then(data => {
        console.log('Success:', data);
        row.dataset.rowId = data.item.id;
        delete row.dataset.isNew;
        headers.forEach((header, i) => {
          row.cells[i].textContent = itemData[header];
        });
        const actionCell = row.cells[headers.length];
        actionCell.innerHTML = `
            <button class="remove-button" onclick="removeRow(this)">Remove</button>
            <button class="edit-button" onclick="editRow(this)">Edit</button>
          `;
        alert("Item saved successfully!");
      })
      .catch(error => {
        console.error('Error:', error);
        alert("Error saving item: " + error.message);
        row.remove();
      });
  }
  
  function cancelNewRow(button) {
    const row = button.parentElement.parentElement;
    row.remove();
  }
  
  function editRow(button) {
    const row = button.parentElement.parentElement;
    const cells = row.cells;
    const headers = ["Product", "Category", "Price", "Stock", "Supplier"];
  
    for (let i = 0; i < cells.length - 2; i++) {
      const cell = cells[i];
      const text = cell.textContent;
      cell.innerHTML = `<input type="text" value="${text}">`;
    }
    const expirationDate = cells[cells.length - 1].textContent;
    cells[cells.length - 1].innerHTML = `<input type="date" value="${expirationDate}">`;
  
    button.style.display = 'none';
    const saveButton = document.createElement('button');
    saveButton.textContent = 'Save';
    saveButton.classList.add('save-button');
    saveButton.onclick = () => saveEditedRow(row);
    button.parentElement.appendChild(saveButton);
  }
  
  function saveEditedRow(row) {
    const cells = row.cells;
    const itemData = {};
    const headers = ["Product", "Category", "Price", "Stock", "Supplier"];
    let isValid = true;
  
    for (let i = 0; i < headers.length; i++) {
      const cell = cells[i];
      const input = cell.querySelector('input');
      const value = input.value;
  
      if (headers[i] === "Price" || headers[i] === "Stock") {
        const numValue = Number(value);
        if (isNaN(numValue) || numValue < 0) {
          alert(`Invalid ${headers[i]}. Please enter a non-negative number.`);
          input.focus();
          isValid = false;
          break;
        }
        itemData[headers[i]] = numValue;
      } else {
        itemData[headers[i]] = value;
      }
    }
  
    if (!isValid) return;
    itemData["id"] = row.dataset.rowId;
    itemData["Expiration Date"] = cells[cells.length - 1].querySelector('input').value;
  
    fetch('/update-inventory', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(itemData)
    })
      .then(response => {
        if (!response.ok) {
          return response.json().then(err => {
            throw new Error(JSON.stringify(err) || "Failed to update");
          });
        }
        return response.json();
      })
      .then(data => {
        // Update the table cells with the new values
        for (let i = 0; i < headers.length; i++) {
          const cell = cells[i];
          const input = cell.querySelector('input');
          cell.textContent = input.value; // Or data[headers[i]]
        }
        cells[headers.length].textContent = itemData["Expiration Date"];
  
        // Handle the Save/Edit button toggle
        const saveButton = row.querySelector('.save-button');
        if (saveButton) {
          saveButton.style.display = 'none'; // Hide Save button
        }
  
        const actionCell = row.querySelector('td:last-child');
        const editButton = document.createElement('button');
        editButton.textContent = 'Edit';
        editButton.classList.add('edit-button');
        editButton.onclick = () => editRow(editButton);
        actionCell.appendChild(editButton);
        alert("Item updated successfully!");
      })
      .catch(error => {
        console.error("Update Error:", error);
        try {
          const errorData = JSON.parse(error.message);
          alert("Error updating item: " + errorData.message);
          if (errorData.trace) {
            console.error("Server Traceback:\n" + errorData.trace);
          }
        } catch (jsonError) {
          alert("A general error occurred: " + error);
        }
      });
  }