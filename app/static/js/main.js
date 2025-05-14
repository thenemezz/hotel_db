/**
 * Главный JavaScript файл для гостиничного комплекса
 */

document.addEventListener('DOMContentLoaded', function() {
    // Включаем все tooltips из Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Включаем все popovers из Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Авто-скрытие flash сообщений через 5 секунд
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            } else {
                // Если кнопка закрытия отсутствует, просто скрываем сообщение
                message.style.display = 'none';
            }
        }, 5000);
    });

    // Функция для подтверждения операций удаления
    const confirmDeletion = function(e) {
        if (!confirm('Вы уверены, что хотите удалить этот элемент? Это действие невозможно отменить.')) {
            e.preventDefault();
            return false;
        }
        return true;
    };

    // Добавляем подтверждение удаления к формам без модальных окон
    const deleteForms = document.querySelectorAll('form[action*="delete"]');
    deleteForms.forEach(function(form) {
        // Проверяем, что форма не находится внутри модального окна
        if (!form.closest('.modal')) {
            form.addEventListener('submit', confirmDeletion);
        }
    });

    // Динамическое отображение полей, в зависимости от выбранных опций
    const toggleElements = document.querySelectorAll('[data-toggle-target]');
    toggleElements.forEach(function(element) {
        const targetId = element.getAttribute('data-toggle-target');
        const targetElement = document.getElementById(targetId);

        if (targetElement) {
            if (element.type === 'checkbox') {
                // Обработка чекбоксов
                targetElement.style.display = element.checked ? 'block' : 'none';

                element.addEventListener('change', function() {
                    targetElement.style.display = this.checked ? 'block' : 'none';
                });
            } else if (element.tagName === 'SELECT') {
                // Обработка select
                const toggleValue = element.getAttribute('data-toggle-value');
                targetElement.style.display = element.value === toggleValue ? 'block' : 'none';

                element.addEventListener('change', function() {
                    targetElement.style.display = this.value === toggleValue ? 'block' : 'none';
                });
            }
        }
    });

    // Автоматическое обновление стоимости услуг при выборе типа услуги
    const serviceTypeSelect = document.getElementById('service_type_id');
    const costInput = document.getElementById('cost');

    if (serviceTypeSelect && costInput) {
        serviceTypeSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption.value) {
                // Получаем базовую цену из data-атрибута
                const basePrice = selectedOption.getAttribute('data-price');
                if (basePrice) {
                    costInput.value = basePrice;
                }
            } else {
                costInput.value = '';
            }
        });
    }

    // Валидация дат в формах бронирования
    const checkInDate = document.getElementById('check_in_date');
    const checkOutDate = document.getElementById('check_out_date');

    if (checkInDate && checkOutDate) {
        // Устанавливаем минимальную дату заезда - сегодня
        const today = new Date();
        const formattedToday = today.toISOString().split('T')[0];
        checkInDate.min = formattedToday;

        checkInDate.addEventListener('change', function() {
            // Устанавливаем минимальную дату выезда как дату заезда + 1 день
            const checkIn = new Date(this.value);
            checkIn.setDate(checkIn.getDate() + 1);
            const minCheckOut = checkIn.toISOString().split('T')[0];
            checkOutDate.min = minCheckOut;

            // Если текущая дата выезда раньше минимальной, обновляем её
            if (checkOutDate.value && checkOutDate.value < minCheckOut) {
                checkOutDate.value = minCheckOut;
            }
        });
    }

    // Кнопка для возврата наверх страницы
    const backToTopButton = document.createElement('button');
    backToTopButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopButton.className = 'btn btn-primary back-to-top';
    backToTopButton.style.position = 'fixed';
    backToTopButton.style.bottom = '20px';
    backToTopButton.style.right = '20px';
    backToTopButton.style.display = 'none';
    backToTopButton.style.zIndex = '1000';

    document.body.appendChild(backToTopButton);

    backToTopButton.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    window.addEventListener('scroll', function() {
        if (window.scrollY > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
});