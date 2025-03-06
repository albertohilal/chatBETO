SELECT 
    conv.conversation_id,
    conv.title,
    msg.create_time,
    msg.role AS message_role,
    msg.content AS message_content
FROM iunaorg_chatBeto.conversations conv
LEFT JOIN iunaorg_chatBeto.messages msg
    ON msg.conversation_id = conv.conversation_id
WHERE EXISTS (
    SELECT 1 FROM iunaorg_chatBeto.messages sub_messages
    WHERE sub_messages.conversation_id = conv.conversation_id
    AND sub_messages.content IS NOT NULL
    AND sub_messages.content <> ''
    AND sub_messages.content LIKE '%TU BUSQUEDA%'  /*AQUI VA EL TERMINO DE BUSQUEDA*/
)
AND msg.content IS NOT NULL
AND msg.content <> ''
AND msg.role IN ('user', 'assistant')
ORDER BY conv.conversation_id, msg.create_time ASC;