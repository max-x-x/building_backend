import logging
from api.models.log import Log, LogLevel, LogCategory


def log_message(level, category, message):
    """Создает лог с подробным сообщением на русском языке."""
    Log.objects.create(
        level=level,
        category=category,
        message=message
    )


def log_object_created(object_name, object_address, user_name, user_role):
    """Логирует создание объекта."""
    message = f"Создан новый объект строительства '{object_name}' по адресу '{object_address}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.OBJECT, message)


def log_object_viewed(object_name, user_name, user_role):
    """Логирует просмотр объекта."""
    message = f"Просмотр объекта '{object_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.OBJECT, message)


def log_object_updated(object_name, user_name, user_role, changes=None):
    """Логирует изменение объекта."""
    changes_text = f" Изменения: {changes}" if changes else ""
    message = f"Объект '{object_name}' изменен пользователем {user_name} (роль: {user_role}){changes_text}"
    log_message(LogLevel.INFO, LogCategory.OBJECT, message)


def log_object_status_changed(object_name, old_status, new_status, user_name, user_role, reason=None):
    """Логирует изменение статуса объекта."""
    reason_text = f" Причина: {reason}" if reason else ""
    message = f"Статус объекта '{object_name}' изменен с '{old_status}' на '{new_status}' пользователем {user_name} (роль: {user_role}){reason_text}"
    log_message(LogLevel.INFO, LogCategory.OBJECT, message)


def log_activation_requested(object_name, user_name, user_role, iko_name=None):
    """Логирует запрос активации объекта."""
    iko_text = f" Назначен ИКО: {iko_name}" if iko_name else ""
    message = f"Запрос активации объекта '{object_name}' отправлен пользователем {user_name} (роль: {user_role}){iko_text}"
    log_message(LogLevel.INFO, LogCategory.ACTIVATION, message)


def log_activation_approved(object_name, iko_name, user_role):
    """Логирует одобрение активации объекта."""
    message = f"Активация объекта '{object_name}' одобрена ИКО {iko_name} (роль: {user_role}). Объект переведен в статус 'Активен'"
    log_message(LogLevel.INFO, LogCategory.ACTIVATION, message)


def log_activation_rejected(object_name, iko_name, user_role, reason=None):
    """Логирует отклонение активации объекта."""
    reason_text = f" Причина отклонения: {reason}" if reason else ""
    message = f"Активация объекта '{object_name}' отклонена ИКО {iko_name} (роль: {user_role}){reason_text}"
    log_message(LogLevel.WARNING, LogCategory.ACTIVATION, message)


def log_prescription_created(object_name, prescription_title, user_name, user_role):
    """Логирует создание нарушения."""
    message = f"Создано нарушение '{prescription_title}' для объекта '{object_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.PRESCRIPTION, message)


def log_prescription_fixed(object_name, prescription_title, user_name, user_role):
    """Логирует исправление нарушения."""
    message = f"Нарушение '{prescription_title}' для объекта '{object_name}' исправлено пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.PRESCRIPTION, message)


def log_prescription_verified(object_name, prescription_title, user_name, user_role, approved=True, reason=None):
    """Логирует проверку нарушения."""
    if approved:
        message = f"Нарушение '{prescription_title}' для объекта '{object_name}' подтверждено пользователем {user_name} (роль: {user_role})"
    else:
        reason_text = f" Причина отклонения: {reason}" if reason else ""
        message = f"Нарушение '{prescription_title}' для объекта '{object_name}' отклонено пользователем {user_name} (роль: {user_role}){reason_text}"
    log_message(LogLevel.INFO, LogCategory.PRESCRIPTION, message)


def log_delivery_created(object_name, delivery_id, user_name, user_role):
    """Логирует создание поставки."""
    message = f"Создана поставка #{delivery_id} для объекта '{object_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.DELIVERY, message)


def log_delivery_received(object_name, delivery_id, user_name, user_role):
    """Логирует получение поставки."""
    message = f"Поставка #{delivery_id} для объекта '{object_name}' получена пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.DELIVERY, message)


def log_delivery_accepted(object_name, delivery_id, user_name, user_role):
    """Логирует принятие поставки."""
    message = f"Поставка #{delivery_id} для объекта '{object_name}' принята пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.DELIVERY, message)


def log_delivery_sent_to_lab(object_name, delivery_id, user_name, user_role):
    """Логирует отправку поставки в лабораторию."""
    message = f"Поставка #{delivery_id} для объекта '{object_name}' отправлена в лабораторию пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.DELIVERY, message)


def log_work_plan_created(object_name, work_plan_title, user_name, user_role):
    """Логирует создание графика работ."""
    message = f"Создан график работ '{work_plan_title}' для объекта '{object_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.WORK_PLAN, message)


def log_work_item_completed(object_name, work_item_name, user_name, user_role):
    """Логирует завершение работы."""
    message = f"Работа '{work_item_name}' для объекта '{object_name}' завершена пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.WORK_PLAN, message)


def log_user_login(user_name, user_role, success=True):
    """Логирует вход пользователя."""
    if success:
        message = f"Пользователь {user_name} (роль: {user_role}) успешно вошел в систему"
        log_message(LogLevel.INFO, LogCategory.AUTH, message)
    else:
        message = f"Неудачная попытка входа пользователя {user_name}"
        log_message(LogLevel.WARNING, LogCategory.AUTH, message)


def log_user_logout(user_name, user_role):
    """Логирует выход пользователя."""
    message = f"Пользователь {user_name} (роль: {user_role}) вышел из системы"
    log_message(LogLevel.INFO, LogCategory.AUTH, message)


def log_error(error_message, category=LogCategory.SYSTEM):
    """Логирует ошибку."""
    log_message(LogLevel.ERROR, category, f"Ошибка: {error_message}")


def log_warning(warning_message, category=LogCategory.SYSTEM):
    """Логирует предупреждение."""
    log_message(LogLevel.WARNING, category, f"Предупреждение: {warning_message}")


def log_notification_sent(recipient_email, recipient_name, subject, user_name, user_role):
    """Логирует отправку уведомления."""
    message = f"Отправлено уведомление '{subject}' на {recipient_email} от {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.SYSTEM, message)


def log_notification_failed(recipient_email, subject, error_message, user_name, user_role):
    """Логирует ошибку отправки уведомления."""
    message = f"Ошибка отправки уведомления '{subject}' на {recipient_email}: {error_message}. Отправитель: {user_name} (роль: {user_role})"
    log_message(LogLevel.ERROR, LogCategory.SYSTEM, message)


def log_area_created(area_name, object_name, user_name, user_role):
    """Логирует создание полигона."""
    message = f"Создан полигон '{area_name}' для объекта '{object_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.AREA, message)


def log_area_viewed(area_name, user_name, user_role):
    """Логирует просмотр полигона."""
    message = f"Просмотр полигона '{area_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.AREA, message)


def log_user_created(user_name, user_email, user_role, created_by_name, created_by_role):
    """Логирует создание пользователя."""
    message = f"Создан пользователь {user_name} ({user_email}) с ролью {user_role} пользователем {created_by_name} (роль: {created_by_role})"
    log_message(LogLevel.INFO, LogCategory.USER, message)


def log_user_updated(user_name, user_email, user_role, updated_by_name, updated_by_role):
    """Логирует изменение пользователя."""
    message = f"Пользователь {user_name} ({user_email}) с ролью {user_role} изменен пользователем {updated_by_name} (роль: {updated_by_role})"
    log_message(LogLevel.INFO, LogCategory.USER, message)


def log_daily_checklist_created(object_name, checklist_id, user_name, user_role):
    """Логирует создание ежедневного чек-листа."""
    message = f"Создан ежедневный чек-лист #{checklist_id} для объекта '{object_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.SYSTEM, message)


def log_daily_checklist_reviewed(object_name, checklist_id, user_name, user_role, approved=True):
    """Логирует проверку ежедневного чек-листа."""
    status = "одобрен" if approved else "отклонен"
    message = f"Ежедневный чек-лист #{checklist_id} для объекта '{object_name}' {status} пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.SYSTEM, message)


def log_work_created(object_name, work_title, user_name, user_role):
    """Логирует создание работы."""
    message = f"Создана работа '{work_title}' для объекта '{object_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.SYSTEM, message)


def log_memo_created(object_name, memo_title, user_name, user_role):
    """Логирует создание мемо."""
    message = f"Создано мемо '{memo_title}' для объекта '{object_name}' пользователем {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.SYSTEM, message)
