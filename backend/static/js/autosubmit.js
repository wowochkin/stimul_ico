(function () {
    if (typeof document === 'undefined') {
        return;
    }

    const setupAutoSubmit = (form) => {
        const defaultDelay = parseInt(form.dataset.autosubmitDelay || '400', 10);
        let typingTimer = null;
        let submitting = false;

        const submitForm = () => {
            if (submitting) {
                return;
            }
            submitting = true;
            if (typeof form.requestSubmit === 'function') {
                form.requestSubmit();
            } else {
                form.submit();
            }
        };

        const scheduleSubmit = (delay) => {
            clearTimeout(typingTimer);
            typingTimer = setTimeout(submitForm, Math.max(delay, 0));
        };

        const resolveDelay = (target) => {
            const value = target.dataset.autosubmitDelay || target.form?.dataset.autosubmitDelay;
            const parsed = parseInt(value || defaultDelay, 10);
            return Number.isNaN(parsed) ? defaultDelay : parsed;
        };

        const handleInput = (event) => {
            scheduleSubmit(resolveDelay(event.target));
        };

        const handleImmediate = () => {
            scheduleSubmit(0);
        };

        form.querySelectorAll('input, select, textarea').forEach((field) => {
            const tag = field.tagName.toLowerCase();
            if (tag === 'select') {
                field.addEventListener('change', handleImmediate);
            } else {
                field.addEventListener('input', handleInput);
                field.addEventListener('blur', handleImmediate);
            }
        });

        form.addEventListener('submit', () => {
            submitting = false;
            clearTimeout(typingTimer);
        });
    };

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('form[data-autosubmit="true"]').forEach(setupAutoSubmit);
    });
})();
