"""
Database seeding utilities for CrewAI Backend
Provides functionality to populate the database with initial/sample data
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import (
    User, UserRole, APIKey, APIKeyType, Graph, Thread, ThreadStatus,
    Message, MessageType, MessageStatus, Execution, ExecutionStatus, 
    ExecutionPriority, Metric, MetricType, MetricCategory
)
from db_config import SessionLocal, engine
from services.encryption import encryption_service


class DatabaseSeeder:
    """
    Database seeding class that provides methods to populate 
    the database with initial and sample data
    """
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize the seeder with an optional database session"""
        self.session = session or SessionLocal()
        self._should_close_session = session is None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session if we created it"""
        if self._should_close_session:
            self.session.close()
    
    def seed_all(self, clear_existing: bool = False) -> None:
        """
        Seed all data types in the correct order
        
        Args:
            clear_existing: If True, clears existing data before seeding
        """
        try:
            if clear_existing:
                self.clear_all_data()
            
            print("🌱 Starting database seeding...")
            
            # Seed in dependency order
            users = self.seed_users()
            api_keys = self.seed_api_keys(users)
            graphs = self.seed_graphs(users)
            threads = self.seed_threads(users, graphs)
            messages = self.seed_messages(users, threads)
            executions = self.seed_executions(users, graphs)
            metrics = self.seed_metrics(users, executions)
            
            self.session.commit()
            print("✅ Database seeding completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during seeding: {str(e)}")
            self.session.rollback()
            raise
    
    def clear_all_data(self) -> None:
        """Clear all data from all tables (useful for testing)"""
        print("🧹 Clearing existing data...")
        
        # Delete in reverse dependency order, with error handling for missing tables
        try:
            self.session.query(Metric).delete()
        except Exception:
            pass  # Table might not exist yet
        
        try:
            self.session.query(Execution).delete()
        except Exception:
            pass  # Table might not exist yet
        
        try:
            self.session.query(Message).delete()
        except Exception:
            pass  # Table might not exist yet
        
        try:
            self.session.query(Thread).delete()
        except Exception:
            pass  # Table might not exist yet
        
        try:
            self.session.query(Graph).delete()
        except Exception:
            pass  # Table might not exist yet
        
        try:
            self.session.query(APIKey).delete()
        except Exception:
            pass  # Table might not exist yet
        
        try:
            self.session.query(User).delete()
        except Exception:
            pass  # Table might not exist yet
        
        self.session.commit()
        print("✅ Existing data cleared")
    
    def seed_users(self) -> List[User]:
        """Seed default and sample users"""
        print("👥 Seeding users...")
        
        users_data = [
            {
                "email": "admin@crewai.com",
                "password": "admin123",
                "first_name": "Admin",
                "last_name": "User",
                "role": UserRole.ADMIN,
                "is_active": True,
                "is_verified": True
            },
            {
                "email": "developer@crewai.com", 
                "password": "dev123",
                "first_name": "Developer",
                "last_name": "User",
                "role": UserRole.USER,
                "is_active": True,
                "is_verified": True
            },
            {
                "email": "test@crewai.com",
                "password": "test123",
                "first_name": "Test",
                "last_name": "User", 
                "role": UserRole.USER,
                "is_active": True,
                "is_verified": False
            }
        ]
        
        created_users = []
        for user_data in users_data:
            # Check if user already exists
            existing_user = self.session.query(User).filter(
                User.email == user_data["email"]
            ).first()
            
            if not existing_user:
                # Hash password
                password = user_data.pop("password")
                password_hash = bcrypt.hashpw(
                    password.encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                user = User(
                    id=str(uuid.uuid4()),
                    password_hash=password_hash,
                    **user_data
                )
                
                self.session.add(user)
                created_users.append(user)
                print(f"  ✓ Created user: {user.email}")
            else:
                created_users.append(existing_user)
                print(f"  → User already exists: {existing_user.email}")
        
        self.session.flush()  # Flush to get IDs
        return created_users
    
    def seed_api_keys(self, users: List[User]) -> List[APIKey]:
        """Seed sample API keys for users"""
        print("🔑 Seeding API keys...")
        
        created_keys = []
        
        # Create API keys for each user
        for user in users:
            api_keys_data = [
                {
                    "name": "Default Development Key",
                    "key_type": APIKeyType.OPENAI.value,
                    "raw_value": f"sk-dev_{user.email.split('@')[0]}_{uuid.uuid4().hex[:8]}"
                },
                {
                    "name": "Production Key",
                    "key_type": APIKeyType.ANTHROPIC.value, 
                    "raw_value": f"sk-ant-prod_{user.email.split('@')[0]}_{uuid.uuid4().hex[:8]}"
                }
            ]
            
            for key_data in api_keys_data:
                # Check if key already exists
                existing_key = self.session.query(APIKey).filter(
                    APIKey.user_id == user.id,
                    APIKey.name == key_data["name"]
                ).first()
                
                if not existing_key:
                    raw_value = key_data.pop("raw_value")
                    encrypted_value = encryption_service.encrypt(raw_value)
                    
                    api_key = APIKey(
                        id=str(uuid.uuid4()),
                        user_id=user.id,
                        encrypted_value=encrypted_value,
                        is_active=True,
                        **key_data
                    )
                    
                    self.session.add(api_key)
                    created_keys.append(api_key)
                    print(f"  ✓ Created API key: {key_data['name']} for {user.email}")
                else:
                    created_keys.append(existing_key)
        
        self.session.flush()
        return created_keys
    
    def seed_graphs(self, users: List[User]) -> List[Graph]:
        """Seed sample graphs"""
        print("📊 Seeding graphs...")
        
        sample_graphs = [
            {
                "name": "Hello World CrewAI",
                "description": "A simple hello world CrewAI graph for testing",
                "graph_data": {
                    "nodes": [
                        {
                            "id": "agent_1",
                            "type": "agent",
                            "position": {"x": 100, "y": 100},
                            "data": {
                                "name": "Hello Agent",
                                "role": "greeting_agent",
                                "goal": "Say hello to the world",
                                "backstory": "A friendly agent that greets everyone"
                            }
                        },
                        {
                            "id": "task_1", 
                            "type": "task",
                            "position": {"x": 300, "y": 100},
                            "data": {
                                "name": "Hello Task",
                                "description": "Generate a hello world message",
                                "expected_output": "A friendly greeting message"
                            }
                        }
                    ],
                    "edges": [
                        {
                            "id": "edge_1",
                            "source": "agent_1",
                            "target": "task_1"
                        }
                    ]
                },
                "is_template": False
            },
            {
                "name": "Research Crew Template",
                "description": "Template for research tasks with multiple agents",
                "graph_data": {
                    "nodes": [
                        {
                            "id": "researcher",
                            "type": "agent", 
                            "position": {"x": 50, "y": 50},
                            "data": {
                                "name": "Senior Researcher",
                                "role": "research_specialist",
                                "goal": "Conduct thorough research on given topics",
                                "backstory": "Expert researcher with years of experience"
                            }
                        },
                        {
                            "id": "writer",
                            "type": "agent",
                            "position": {"x": 50, "y": 200},
                            "data": {
                                "name": "Content Writer", 
                                "role": "content_creator",
                                "goal": "Create engaging content from research",
                                "backstory": "Skilled writer who transforms data into stories"
                            }
                        },
                        {
                            "id": "research_task",
                            "type": "task",
                            "position": {"x": 300, "y": 50},
                            "data": {
                                "name": "Research Task",
                                "description": "Research the given topic thoroughly",
                                "expected_output": "Comprehensive research report"
                            }
                        },
                        {
                            "id": "writing_task",
                            "type": "task", 
                            "position": {"x": 300, "y": 200},
                            "data": {
                                "name": "Writing Task",
                                "description": "Write content based on research",
                                "expected_output": "Well-written article or report"
                            }
                        }
                    ],
                    "edges": [
                        {"id": "edge_1", "source": "researcher", "target": "research_task"},
                        {"id": "edge_2", "source": "writer", "target": "writing_task"},
                        {"id": "edge_3", "source": "research_task", "target": "writing_task"}
                    ]
                },
                "is_template": True
            }
        ]
        
        created_graphs = []
        for i, graph_data in enumerate(sample_graphs):
            user = users[i % len(users)]  # Distribute graphs among users
            
            # Check if graph already exists
            existing_graph = self.session.query(Graph).filter(
                Graph.user_id == user.id,
                Graph.name == graph_data["name"]
            ).first()
            
            if not existing_graph:
                graph = Graph(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    **graph_data
                )
                
                self.session.add(graph)
                created_graphs.append(graph)
                print(f"  ✓ Created graph: {graph.name}")
            else:
                created_graphs.append(existing_graph)
        
        self.session.flush()
        return created_graphs
    
    def seed_threads(self, users: List[User], graphs: List[Graph]) -> List[Thread]:
        """Seed sample threads"""
        print("🧵 Seeding threads...")
        
        created_threads = []
        for i, graph in enumerate(graphs):
            user = users[i % len(users)]
            
            thread_data = {
                "name": f"Test Thread for {graph.name}",
                "description": f"Sample thread for testing {graph.name}",
                "status": ThreadStatus.ACTIVE,
                "thread_config": {"source": "seeder", "purpose": "testing"}
            }
            
            # Check if thread already exists
            existing_thread = self.session.query(Thread).filter(
                Thread.graph_id == graph.id,
                Thread.name == thread_data["name"]
            ).first()
            
            if not existing_thread:
                thread = Thread(
                    id=str(uuid.uuid4()),
                    graph_id=graph.id,
                    **thread_data
                )
                
                self.session.add(thread)
                created_threads.append(thread)
                print(f"  ✓ Created thread: {thread.name}")
            else:
                created_threads.append(existing_thread)
        
        self.session.flush()
        return created_threads
    
    def seed_messages(self, users: List[User], threads: List[Thread]) -> List[Message]:
        """Seed sample messages"""
        print("💬 Seeding messages...")
        
        created_messages = []
        for thread in threads:
            # Note: Message doesn't have user_id field, only thread_id
            
            messages_data = [
                {
                    "message_type": MessageType.USER,
                    "content": "Hello, please run this graph for me",
                    "status": MessageStatus.COMPLETED,
                    "message_metadata": {"timestamp": datetime.utcnow().isoformat()}
                },
                {
                    "message_type": MessageType.SYSTEM,
                    "content": "Graph execution started",
                    "status": MessageStatus.COMPLETED,
                    "message_metadata": {"event": "execution_started"}
                }
            ]
            
            for seq_num, msg_data in enumerate(messages_data, 1):
                message = Message(
                    id=str(uuid.uuid4()),
                    thread_id=thread.id,
                    content=msg_data["content"],
                    message_type=msg_data["message_type"].value,
                    status=msg_data["status"].value,
                    message_metadata=msg_data["message_metadata"],
                    sequence_number=seq_num
                )
                
                self.session.add(message)
                created_messages.append(message)
        
        print(f"  ✓ Created {len(created_messages)} messages")
        self.session.flush()
        return created_messages
    
    def seed_executions(self, users: List[User], graphs: List[Graph]) -> List[Execution]:
        """Seed sample executions"""
        print("⚡ Seeding executions...")
        
        created_executions = []
        for graph in graphs:
            # Note: Execution doesn't have user_id, it gets user through graph relationship
            
            execution_data = {
                "execution_name": f"Sample execution for {graph.name}",
                "status": ExecutionStatus.COMPLETED,
                "priority": ExecutionPriority.NORMAL,
                "execution_config": {"message": "Hello world"},
                "result_data": {"result": "Hello from CrewAI!"},
                "output_logs": "Execution started\nAgents initialized\nTasks completed",
                "started_at": datetime.utcnow() - timedelta(minutes=5),
                "completed_at": datetime.utcnow(),
                "progress_percentage": 100
            }
            
            execution = Execution(
                id=str(uuid.uuid4()),
                graph_id=graph.id,
                **execution_data
            )
            
            self.session.add(execution)
            created_executions.append(execution)
        
        print(f"  ✓ Created {len(created_executions)} executions")
        self.session.flush()
        return created_executions
    
    def seed_metrics(self, users: List[User], executions: List[Execution]) -> List[Metric]:
        """Seed sample metrics"""
        print("📈 Seeding metrics...")
        
        created_metrics = []
        for execution in executions:
            # Get user through execution -> graph -> user relationship
            user = next(u for u in users if str(u.id) == str(execution.graph.user_id))
            
            metrics_data = [
                {
                    "metric_name": "execution_time",
                    "metric_type": MetricType.COUNTER,
                    "category": MetricCategory.PERFORMANCE,
                    "value": 4.5,
                    "unit": "seconds",
                    "tags": {"execution_id": execution.id}
                },
                {
                    "metric_name": "tokens_used",
                    "metric_type": MetricType.GAUGE,
                    "category": MetricCategory.RESOURCE,
                    "value": 1250.0,
                    "unit": "tokens",
                    "tags": {"execution_id": execution.id}
                },
                {
                    "metric_name": "success_rate",
                    "metric_type": MetricType.GAUGE,
                    "category": MetricCategory.BUSINESS,
                    "value": 100.0,
                    "unit": "percentage",
                    "tags": {"execution_id": execution.id}
                }
            ]
            
            for metric_data in metrics_data:
                metric = Metric(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    execution_id=execution.id,
                    **metric_data
                )
                
                self.session.add(metric)
                created_metrics.append(metric)
        
        print(f"  ✓ Created {len(created_metrics)} metrics")
        self.session.flush()
        return created_metrics


def seed_database(clear_existing: bool = False) -> None:
    """
    Convenience function to seed the database
    
    Args:
        clear_existing: If True, clears existing data before seeding
    """
    with DatabaseSeeder() as seeder:
        seeder.seed_all(clear_existing=clear_existing)


def clear_database() -> None:
    """Convenience function to clear all database data"""
    with DatabaseSeeder() as seeder:
        seeder.clear_all_data()


if __name__ == "__main__":
    import sys
    
    # Command line interface for seeding
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "seed":
            clear = "--clear" in sys.argv
            seed_database(clear_existing=clear)
        elif command == "clear":
            clear_database()
        else:
            print("Usage: python seeder.py [seed|clear] [--clear]")
            print("  seed: Seed the database with sample data")
            print("  clear: Clear all data from the database") 
            print("  --clear: Clear existing data before seeding")
    else:
        # Default action
        seed_database() 