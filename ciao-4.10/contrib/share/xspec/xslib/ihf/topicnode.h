
struct topicnode { char *topic;
                   Textnode *text;
                   struct topicnode *parent;
                   struct topicnode *subtopic;
                   struct topicnode *next;
                 };

typedef struct topicnode Topicnode;
