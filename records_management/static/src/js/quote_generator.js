document.addEventListener('DOMContentLoaded', function() {
    // Initial line
    addQuoteLine();
});

function addQuoteLine() {
    const linesContainer = document.getElementById('quote_lines');
    const lineIndex = linesContainer.children.length + 1;

    const lineDiv = document.createElement('div');
    lineDiv.className = 'row mb-3 quote-line';
    lineDiv.innerHTML = `
        <div class="col-md-4">
            <label for="line_type_${lineIndex}">Service Type</label>
            <select name="line_type_${lineIndex}" id="line_type_${lineIndex}" class="form-control">
                <option value="shredding">Shredding Boxes</option>
                <option value="pickup">Pickup Service</option>
            </select>
        </div>
        <div class="col-md-3">
            <label for="line_qty_${lineIndex}">Quantity</label>
            <input type="number" name="line_qty_${lineIndex}" id="line_qty_${lineIndex}" class="form-control" value="1" min="1">
        </div>
        <div class="col-md-3">
            <label for="line_rate_${lineIndex}">Rate (auto)</label>
            <input type="text" id="line_rate_${lineIndex}" class="form-control" readonly>
        </div>
        <div class="col-md-2 d-flex align-items-end">
            <button type="button" class="btn btn-danger btn-sm" onclick="removeQuoteLine(this)">
                <i class="fa fa-trash"></i>
            </button>
        </div>
    `;
    linesContainer.appendChild(lineDiv);
}

function removeQuoteLine(button) {
    button.closest('.quote-line').remove();
}
