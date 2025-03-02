/*Se puede usar en Workbench o PhpMyAdmin*/
CREATE TABLE conversations (
    conversation_id VARCHAR(50) PRIMARY KEY,
    default_model_slug VARCHAR(50),
    is_archived BOOLEAN
);

CREATE TABLE messages (
    id VARCHAR(50) PRIMARY KEY,
    conversation_id VARCHAR(50),
    author_role ENUM('user', 'assistant'),
    create_time TIMESTAMP,
    content TEXT,
    parent_id VARCHAR(50),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    FOREIGN KEY (parent_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE TABLE message_relations (
    parent_id VARCHAR(50),
    child_id VARCHAR(50),
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES messages(id) ON DELETE CASCADE
);

