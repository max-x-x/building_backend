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


# === ЛОГИРОВАНИЕ ОПЕРАЦИЙ С ФАЙЛОВЫМ ХРАНИЛИЩЕМ ===

def log_file_upload_success(file_type, entity_name, entity_id, folder_url, user_name, user_role, file_count=1):
    """Логирует успешную загрузку файлов в файловое хранилище."""
    files_text = f"{file_count} файл(ов)" if file_count > 1 else "файл"
    message = f"Успешно загружен {files_text} {file_type} для '{entity_name}' (ID: {entity_id}) в файловое хранилище: {folder_url}. Пользователь: {user_name} (роль: {user_role})"
    log_message(LogLevel.INFO, LogCategory.FILE_STORAGE, message)


def log_file_upload_failed(file_type, entity_name, entity_id, error_message, user_name, user_role, file_count=1):
    """Логирует ошибку загрузки файлов в файловое хранилище."""
    files_text = f"{file_count} файл(ов)" if file_count > 1 else "файл"
    message = f"Ошибка загрузки {files_text} {file_type} для '{entity_name}' (ID: {entity_id}): {error_message}. Пользователь: {user_name} (роль: {user_role})"
    log_message(LogLevel.ERROR, LogCategory.FILE_STORAGE, message)


def log_file_storage_connection_failed(operation, error_message):
    """Логирует ошибку подключения к файловому хранилищу."""
    message = f"Ошибка подключения к файловому хранилищу при операции '{operation}': {error_message}"
    log_message(LogLevel.ERROR, LogCategory.FILE_STORAGE, message)


def log_file_storage_timeout(operation, timeout_seconds):
    """Логирует таймаут при работе с файловым хранилищем."""
    message = f"Таймаут при операции '{operation}' с файловым хранилищем (превышено {timeout_seconds} секунд)"
    log_message(LogLevel.WARNING, LogCategory.FILE_STORAGE, message)


def log_file_storage_response_error(operation, status_code, response_text):
    """Логирует ошибку ответа от файлового хранилища."""
    message = f"Ошибка ответа от файлового хранилища при операции '{operation}': HTTP {status_code}, ответ: {response_text[:200]}..."
    log_message(LogLevel.ERROR, LogCategory.FILE_STORAGE, message)


def log_object_documents_uploaded(object_name, object_id, folder_url, user_name, user_role, file_count):
    """Логирует загрузку документов объекта."""
    log_file_upload_success("документов объекта", object_name, object_id, folder_url, user_name, user_role, file_count)


def log_object_documents_upload_failed(object_name, object_id, error_message, user_name, user_role, file_count):
    """Логирует ошибку загрузки документов объекта."""
    log_file_upload_failed("документов объекта", object_name, object_id, error_message, user_name, user_role, file_count)


def log_violation_photos_uploaded(prescription_title, prescription_id, folder_url, user_name, user_role, file_count):
    """Логирует загрузку фото нарушения."""
    log_file_upload_success("фото нарушения", prescription_title, prescription_id, folder_url, user_name, user_role, file_count)


def log_violation_photos_upload_failed(prescription_title, prescription_id, error_message, user_name, user_role, file_count):
    """Логирует ошибку загрузки фото нарушения."""
    log_file_upload_failed("фото нарушения", prescription_title, prescription_id, error_message, user_name, user_role, file_count)


def log_fix_photos_uploaded(prescription_title, prescription_id, folder_url, user_name, user_role, file_count):
    """Логирует загрузку фото исправления."""
    log_file_upload_success("фото исправления", prescription_title, prescription_id, folder_url, user_name, user_role, file_count)


def log_fix_photos_upload_failed(prescription_title, prescription_id, error_message, user_name, user_role, file_count):
    """Логирует ошибку загрузки фото исправления."""
    log_file_upload_failed("фото исправления", prescription_title, prescription_id, error_message, user_name, user_role, file_count)


def log_invoice_photos_uploaded(delivery_id, folder_url, user_name, user_role, file_count):
    """Логирует загрузку фото накладных."""
    log_file_upload_success("фото накладных", f"поставка #{delivery_id}", delivery_id, folder_url, user_name, user_role, file_count)


def log_invoice_photos_upload_failed(delivery_id, error_message, user_name, user_role, file_count):
    """Логирует ошибку загрузки фото накладных."""
    log_file_upload_failed("фото накладных", f"поставка #{delivery_id}", delivery_id, error_message, user_name, user_role, file_count)
