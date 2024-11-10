```
attendance-slack-bot/
├── config/
│   └── config.yaml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── constants/
│   │   └── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── attendance.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── firestore_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── attendance_service.py
│   ├── slack/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   └── attendance_commands.py
│   │   └── message_builder.py
│   └── utils/
│       ├── __init__.py
│       └── time_utils.py
├── requirements.txt
└── README.md
```