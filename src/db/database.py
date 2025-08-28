import sqlite3
import os
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any

class InsuranceDatabase:
    def __init__(self, db_path: str = "data/insurance.db"):
        self.db_path = db_path
        self.ensure_data_dir()
        self.init_database()
    
    def ensure_data_dir(self):
        """Ensure the data directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """Initialize database with tables and seed data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            self.create_tables(conn)
            self.seed_initial_data(conn)
    
    def create_tables(self, conn: sqlite3.Connection):
        """Create all necessary tables"""
        # Agents table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                notes TEXT
            )
        """)
        
        # Buildings table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                address TEXT,
                notes TEXT
            )
        """)
        
        # Policies table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                agent_id INTEGER NOT NULL,
                carrier TEXT NOT NULL,
                policy_number TEXT NOT NULL,
                coverage_json TEXT,
                premium REAL,
                eff_date DATE,
                exp_date DATE,
                file_path TEXT,
                notes TEXT,
                FOREIGN KEY (building_id) REFERENCES buildings (id),
                FOREIGN KEY (agent_id) REFERENCES agents (id)
            )
        """)
        
        # Policy text storage for RAG
        conn.execute("""
            CREATE TABLE IF NOT EXISTS policy_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                policy_id INTEGER NOT NULL,
                extracted_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (policy_id) REFERENCES policies (id)
            )
        """)
        
        conn.commit()
    
    def seed_initial_data(self, conn: sqlite3.Connection):
        """Seed database with initial agents and buildings"""
        # Check if data already exists
        cursor = conn.execute("SELECT COUNT(*) FROM agents")
        if cursor.fetchone()[0] > 0:
            return  # Data already seeded
        
        # Create 8 agents (A1 to A8)
        agents = [
            ("A1", "John Smith", "john.smith@insurance.com", "555-0101", "Senior agent, specializes in commercial"),
            ("A2", "Sarah Johnson", "sarah.j@insurance.com", "555-0102", "New agent, learning commercial policies"),
            ("A3", "Mike Davis", "mike.davis@insurance.com", "555-0103", "Experienced in residential"),
            ("A4", "Lisa Wilson", "lisa.w@insurance.com", "555-0104", "Commercial property specialist"),
            ("A5", "Tom Brown", "tom.brown@insurance.com", "555-0105", "Multi-line agent"),
            ("A6", "Emma Garcia", "emma.g@insurance.com", "555-0106", "Claims specialist"),
            ("A7", "David Lee", "david.lee@insurance.com", "555-0107", "Underwriting expert"),
            ("A8", "Anna Martinez", "anna.m@insurance.com", "555-0108", "Risk management focus")
        ]
        
        for agent in agents:
            conn.execute("""
                INSERT INTO agents (name, email, phone, notes)
                VALUES (?, ?, ?, ?)
            """, agent[1:])
        
        # Create 27 buildings (B1 to B27) with 3-digit codes + street names
        buildings = [
            ("B001", "Main Street Plaza", "123 Main Street, Downtown", "High-traffic commercial building"),
            ("B002", "Oak Avenue Complex", "456 Oak Avenue, Midtown", "Mixed-use development"),
            ("B003", "Riverside Tower", "789 Riverside Drive", "Luxury residential tower"),
            ("B004", "Industrial Park Unit A", "100 Industrial Blvd", "Manufacturing facility"),
            ("B005", "Shopping Center East", "200 Commerce Way", "Retail complex"),
            ("B006", "Office Park Building 1", "300 Business Circle", "Corporate headquarters"),
            ("B007", "Harbor View Condos", "400 Harbor Road", "Waterfront residential"),
            ("B008", "Tech Campus Building A", "500 Innovation Drive", "Software company offices"),
            ("B009", "Medical Center West", "600 Health Avenue", "Healthcare facility"),
            ("B010", "University Hall", "700 Education Street", "Academic building"),
            ("B011", "Airport Hotel", "800 Travel Lane", "Hospitality property"),
            ("B012", "Warehouse District Unit 1", "900 Storage Road", "Logistics facility"),
            ("B013", "Downtown Mall", "1000 Urban Plaza", "Shopping mall"),
            ("B014", "Residential Complex North", "1100 Home Street", "Apartment complex"),
            ("B015", "Business Park Tower", "1200 Corporate Drive", "Office building"),
            ("B016", "Industrial Complex B", "1300 Factory Lane", "Manufacturing plant"),
            ("B017", "Retail Strip Center", "1400 Shopping Blvd", "Strip mall"),
            ("B018", "Residential Tower South", "1500 Living Way", "High-rise apartments"),
            ("B019", "Office Complex East", "1600 Work Street", "Business center"),
            ("B020", "Industrial Warehouse", "1700 Storage Avenue", "Distribution center"),
            ("B021", "Shopping Plaza West", "1800 Retail Road", "Shopping center"),
            ("B022", "Residential Community", "1900 Family Lane", "Suburban homes"),
            ("B023", "Business District Building", "2000 Commerce Street", "Financial district"),
            ("B024", "Industrial Zone Unit C", "2100 Production Way", "Industrial facility"),
            ("B025", "Retail Center North", "2200 Market Street", "Retail complex"),
            ("B026", "Residential Tower East", "2300 Home Avenue", "Luxury apartments"),
            ("B027", "Office Park Building 2", "2400 Business Drive", "Corporate offices")
        ]
        
        for building in buildings:
            conn.execute("""
                INSERT INTO buildings (code, name, address, notes)
                VALUES (?, ?, ?, ?)
            """, building)
        
        # Randomly assign buildings to agents (simple distribution)
        import random
        building_ids = list(range(1, 28))  # 27 buildings
        agent_ids = list(range(1, 9))      # 8 agents
        
        # Distribute buildings among agents
        for building_id in building_ids:
            agent_id = random.choice(agent_ids)
            # Create a sample policy for each building
            conn.execute("""
                INSERT INTO policies (building_id, agent_id, carrier, policy_number, 
                                   coverage_json, premium, eff_date, exp_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                building_id,
                agent_id,
                random.choice(["State Farm", "Allstate", "Progressive", "Geico", "Liberty Mutual"]),
                f"POL-{building_id:04d}-{random.randint(2020, 2024)}",
                json.dumps({
                    "property": random.choice([1000000, 2000000, 5000000]),
                    "liability": random.choice([500000, 1000000, 2000000]),
                    "deductible": random.choice([1000, 2500, 5000])
                }),
                random.uniform(5000, 25000),
                datetime.now().date() - timedelta(days=random.randint(0, 365)),
                datetime.now().date() + timedelta(days=random.randint(30, 730)),
                f"Sample policy for {buildings[building_id-1][1]}"
            ))
        
        conn.commit()
    
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM agents ORDER BY name")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_buildings(self) -> List[Dict[str, Any]]:
        """Get all buildings"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM buildings ORDER BY code")
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_policies(self) -> List[Dict[str, Any]]:
        """Get all policies with building and agent info"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT p.*, b.code as building_code, b.name as building_name,
                       a.name as agent_name
                FROM policies p
                JOIN buildings b ON p.building_id = b.id
                JOIN agents a ON p.agent_id = a.id
                ORDER BY a.name, b.code
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_agent_building_matrix(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get agent-to-building matrix for table display"""
        policies = self.get_policies()
        matrix = {}
        
        for policy in policies:
            agent_name = policy['agent_name']
            if agent_name not in matrix:
                matrix[agent_name] = []
            
            matrix[agent_name].append({
                'building_code': policy['building_code'],
                'building_name': policy['building_name'],
                'building_id': policy['building_id'],
                'policy_id': policy['id'],
                'notes': policy['notes'],
                'exp_date': policy['exp_date']
            })
        
        return matrix
    
    def update_policy_agent(self, policy_id: int, new_agent_id: int):
        """Update which agent a policy is assigned to"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE policies SET agent_id = ? WHERE id = ?
            """, (new_agent_id, policy_id))
            conn.commit()
    
    def add_policy(self, building_id: int, agent_id: int, carrier: str, 
                   policy_number: str, coverage_json: str, premium: float,
                   eff_date: str, exp_date: str, file_path: str = None, notes: str = None):
        """Add a new policy"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO policies (building_id, agent_id, carrier, policy_number,
                                   coverage_json, premium, eff_date, exp_date, file_path, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (building_id, agent_id, carrier, policy_number, coverage_json,
                  premium, eff_date, exp_date, file_path, notes))
            conn.commit()
            return cursor.lastrowid
    
    def add_agent(self, name: str, email: str = None, phone: str = None, notes: str = None):
        """Add a new agent"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO agents (name, email, phone, notes)
                VALUES (?, ?, ?, ?)
            """, (name, email, phone, notes))
            conn.commit()
            return cursor.lastrowid
    
    def add_building(self, code: str, name: str, address: str = None, notes: str = None):
        """Add a new building"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO buildings (code, name, address, notes)
                VALUES (?, ?, ?, ?)
            """, (code, name, address, notes))
            conn.commit()
            return cursor.lastrowid
    
    def get_expiring_policies(self, days_threshold: int = 60) -> List[Dict[str, Any]]:
        """Get policies expiring within specified days"""
        with sqlite3.connect(self.db_path) as conn:
            threshold_date = datetime.now().date() + timedelta(days=days_threshold)
            cursor = conn.execute("""
                SELECT p.*, b.code as building_code, b.name as building_name,
                       a.name as agent_name, a.email as agent_email
                FROM policies p
                JOIN buildings b ON p.building_id = b.id
                JOIN agents a ON p.agent_id = a.id
                WHERE p.exp_date <= ? AND p.exp_date > ?
                ORDER BY p.exp_date
            """, (threshold_date, datetime.now().date()))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def store_policy_text(self, policy_id: int, extracted_text: str):
        """Store extracted text from policy PDF for RAG"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO policy_texts (policy_id, extracted_text)
                VALUES (?, ?)
            """, (policy_id, extracted_text))
            conn.commit()
    
    def get_policy_texts(self) -> List[Dict[str, Any]]:
        """Get all stored policy texts for RAG"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT pt.*, p.policy_number, b.code as building_code
                FROM policy_texts pt
                JOIN policies p ON pt.policy_id = p.id
                JOIN buildings b ON p.building_id = b.id
                ORDER BY pt.created_at DESC
            """)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
