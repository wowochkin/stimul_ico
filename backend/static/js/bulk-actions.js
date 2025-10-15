(function () {
    if (typeof document === 'undefined') {
        return;
    }

    document.addEventListener('DOMContentLoaded', function () {
        const selectAll = document.getElementById('select-all-requests');
        const checkboxes = Array.from(document.querySelectorAll('.request-checkbox'));
        const bulkButton = document.getElementById('bulk-delete-btn');

        if (!selectAll || checkboxes.length === 0 || !bulkButton) {
            return;
        }

        const updateState = () => {
            const checkedCount = checkboxes.filter((cb) => cb.checked).length;
            bulkButton.disabled = checkedCount === 0;
            if (checkedCount === 0) {
                selectAll.checked = false;
                selectAll.indeterminate = false;
            } else if (checkedCount === checkboxes.length) {
                selectAll.checked = true;
                selectAll.indeterminate = false;
            } else {
                selectAll.indeterminate = true;
            }
        };

        selectAll.addEventListener('change', () => {
            const targetState = selectAll.checked;
            checkboxes.forEach((checkbox) => {
                if (!checkbox.disabled) {
                    checkbox.checked = targetState;
                }
            });
            updateState();
        });

        checkboxes.forEach((checkbox) => {
            checkbox.addEventListener('change', updateState);
        });

        updateState();
    });
})();
