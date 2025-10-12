SELECT 
 `messages`.`role`,
`conversations`.`title`,
`messages`.`parts`
FROM iunaorg_chatBeto.messages
right join `conversations`
on `messages`.`conversation_id` like `conversations`.`conversation_id`

where `conversations`.`title` LIKE "%Whatsapp-Welcome Message Creation%"

order by `messages`.`create_time`