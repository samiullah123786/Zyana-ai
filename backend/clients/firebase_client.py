"""Firebase Admin SDK client for Vidify HQ Dashboard integration.

This client enables Zyana to interact with the Vidify HQ Firebase Firestore
database, allowing voice/text commands to manage:
- Clients
- Projects
- Team members
- Transactions (income/expenses)
- Salary payments
"""
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from google.cloud import firestore
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Firebase Firestore client for Vidify HQ Dashboard."""
    
    def __init__(self):
        """Initialize Firebase Admin SDK."""
        self.db = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Firestore connection."""
        try:
            # Method 1: Load from environment variable (JSON string)
            firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")
            
            if firebase_credentials:
                try:
                    creds_dict = json.loads(firebase_credentials)
                    credentials = service_account.Credentials.from_service_account_info(creds_dict)
                    self.db = firestore.Client(
                        project=creds_dict.get("project_id", "vidify-hq"),
                        credentials=credentials
                    )
                    logger.info("✅ Firebase initialized from FIREBASE_CREDENTIALS env var")
                    return
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to parse FIREBASE_CREDENTIALS: {e}")
            
            # Method 2: Load from file path
            firebase_creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if firebase_creds_path and os.path.exists(firebase_creds_path):
                credentials = service_account.Credentials.from_service_account_file(
                    firebase_creds_path
                )
                # Get project ID from credentials file
                with open(firebase_creds_path) as f:
                    creds_data = json.load(f)
                    project_id = creds_data.get("project_id", "vidify-hq")
                
                self.db = firestore.Client(
                    project=project_id,
                    credentials=credentials
                )
                logger.info(f"✅ Firebase initialized from file: {firebase_creds_path}")
                return
            
            # Method 3: Try default credentials (Google Cloud environment)
            try:
                self.db = firestore.Client(project="vidify-hq")
                logger.info("✅ Firebase initialized with default credentials")
            except Exception:
                logger.warning("⚠️ Firebase not initialized - set FIREBASE_CREDENTIALS env var")
                self.db = None
                
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {e}")
            self.db = None
    
    @property
    def is_connected(self) -> bool:
        """Check if Firebase is connected."""
        return self.db is not None
    
    # ==================== CLIENTS ====================
    
    async def add_client(
        self,
        name: str,
        email: str = "",
        company: str = "",
        status: str = "active"
    ) -> Dict[str, Any]:
        """Add a new client to Vidify HQ.
        
        Args:
            name: Client name
            email: Client email
            company: Company name
            status: active or inactive
            
        Returns:
            Dict with client data and ID
        """
        if not self.db:
            return {"success": False, "error": "Firebase not connected"}
        
        try:
            client_data = {
                "name": name,
                "email": email,
                "company": company,
                "totalPaid": 0,
                "totalDue": 0,
                "projects": [],
                "status": status,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection("clients").document()
            doc_ref.set(client_data)
            
            logger.info(f"✅ Added client: {name} (ID: {doc_ref.id})")
            
            return {
                "success": True,
                "id": doc_ref.id,
                "name": name,
                "company": company
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add client: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_clients(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all clients or filter by status.
        
        Args:
            status: Optional filter (active/inactive)
            
        Returns:
            List of clients
        """
        if not self.db:
            return []
        
        try:
            query = self.db.collection("clients")
            if status:
                query = query.where("status", "==", status)
            
            docs = query.stream()
            clients = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                clients.append(data)
            
            return clients
            
        except Exception as e:
            logger.error(f"❌ Failed to get clients: {e}")
            return []
    
    async def find_client_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a client by name (case-insensitive partial match).
        
        Args:
            name: Client name to search
            
        Returns:
            Client data or None
        """
        if not self.db:
            return None
        
        try:
            # Get all clients and search (Firestore doesn't support case-insensitive search)
            docs = self.db.collection("clients").stream()
            
            name_lower = name.lower()
            for doc in docs:
                data = doc.to_dict()
                if name_lower in data.get("name", "").lower():
                    data["id"] = doc.id
                    return data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to find client: {e}")
            return None
    
    # ==================== PROJECTS ====================
    
    async def add_project(
        self,
        name: str,
        client_id: str,
        total_amount: float = 0,
        status: str = "Pending"
    ) -> Dict[str, Any]:
        """Add a new project.
        
        Args:
            name: Project name
            client_id: Client Firestore ID
            total_amount: Total project amount
            status: Pending, In Progress, or Completed
            
        Returns:
            Dict with project data and ID
        """
        if not self.db:
            return {"success": False, "error": "Firebase not connected"}
        
        try:
            project_data = {
                "name": name,
                "clientId": client_id,
                "totalAmount": total_amount,
                "paidAmount": 0,
                "status": status,
                "assignedTeam": [],
                "startDate": firestore.SERVER_TIMESTAMP,
                "dueDate": None,
                "milestones": [],
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection("projects").document()
            doc_ref.set(project_data)
            
            # Update client's projects array
            client_ref = self.db.collection("clients").document(client_id)
            client_ref.update({
                "projects": firestore.ArrayUnion([doc_ref.id]),
                "totalDue": firestore.Increment(total_amount)
            })
            
            logger.info(f"✅ Added project: {name} (ID: {doc_ref.id})")
            
            return {
                "success": True,
                "id": doc_ref.id,
                "name": name,
                "clientId": client_id
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add project: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all projects or filter by status."""
        if not self.db:
            return []
        
        try:
            query = self.db.collection("projects")
            if status:
                query = query.where("status", "==", status)
            
            docs = query.stream()
            projects = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                projects.append(data)
            
            return projects
            
        except Exception as e:
            logger.error(f"❌ Failed to get projects: {e}")
            return []
    
    # ==================== TRANSACTIONS ====================
    
    async def add_transaction(
        self,
        transaction_type: str,  # "income" or "expense"
        amount: float,
        description: str,
        category: str = "General",
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        team_member_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a transaction (income or expense).
        
        Args:
            transaction_type: "income" or "expense"
            amount: Transaction amount
            description: Description
            category: Category (Salary, Equipment, Marketing, etc.)
            client_id: Optional client ID for income
            project_id: Optional project ID
            team_member_id: Optional team member ID for salary
            
        Returns:
            Dict with transaction data and ID
        """
        if not self.db:
            return {"success": False, "error": "Firebase not connected"}
        
        try:
            transaction_data = {
                "type": transaction_type,
                "amount": amount,
                "description": description,
                "category": category,
                "date": firestore.SERVER_TIMESTAMP,
                "clientId": client_id,
                "projectId": project_id,
                "teamMemberId": team_member_id,
                "createdAt": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection("transactions").document()
            doc_ref.set(transaction_data)
            
            # Update related records for income
            if transaction_type == "income" and client_id:
                client_ref = self.db.collection("clients").document(client_id)
                client_ref.update({
                    "totalPaid": firestore.Increment(amount)
                })
            
            if transaction_type == "income" and project_id:
                project_ref = self.db.collection("projects").document(project_id)
                project_ref.update({
                    "paidAmount": firestore.Increment(amount)
                })
            
            logger.info(f"✅ Added {transaction_type}: {amount} - {description}")
            
            return {
                "success": True,
                "id": doc_ref.id,
                "type": transaction_type,
                "amount": amount,
                "description": description
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add transaction: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== TEAM MEMBERS ====================
    
    async def add_team_member(
        self,
        name: str,
        role: str = "Editor",
        salary: float = 0,
        email: str = ""
    ) -> Dict[str, Any]:
        """Add a team member.
        
        Args:
            name: Team member name
            role: Editor, Manager, Partner, or Intern
            salary: Monthly salary
            email: Email address
            
        Returns:
            Dict with team member data and ID
        """
        if not self.db:
            return {"success": False, "error": "Firebase not connected"}
        
        try:
            member_data = {
                "name": name,
                "email": email,
                "role": role,
                "salary": salary,
                "lastPayment": None,
                "totalPaid": 0,
                "status": "active",
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection("team").document()
            doc_ref.set(member_data)
            
            logger.info(f"✅ Added team member: {name} ({role})")
            
            return {
                "success": True,
                "id": doc_ref.id,
                "name": name,
                "role": role
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to add team member: {e}")
            return {"success": False, "error": str(e)}
    
    async def find_team_member_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a team member by name."""
        if not self.db:
            return None
        
        try:
            docs = self.db.collection("team").stream()
            
            name_lower = name.lower()
            for doc in docs:
                data = doc.to_dict()
                if name_lower in data.get("name", "").lower():
                    data["id"] = doc.id
                    return data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to find team member: {e}")
            return None
    
    async def pay_salary(
        self,
        member_id: str,
        amount: float
    ) -> Dict[str, Any]:
        """Pay salary to a team member.
        
        Args:
            member_id: Team member Firestore ID
            amount: Salary amount
            
        Returns:
            Dict with payment result
        """
        if not self.db:
            return {"success": False, "error": "Firebase not connected"}
        
        try:
            # Get team member name
            member_doc = self.db.collection("team").document(member_id).get()
            member_name = member_doc.to_dict().get("name", "Team member") if member_doc.exists else "Team member"
            
            # Update team member
            member_ref = self.db.collection("team").document(member_id)
            member_ref.update({
                "lastPayment": firestore.SERVER_TIMESTAMP,
                "totalPaid": firestore.Increment(amount),
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
            
            # Add salary transaction
            await self.add_transaction(
                transaction_type="expense",
                amount=amount,
                description=f"Salary payment - {member_name}",
                category="Salary",
                team_member_id=member_id
            )
            
            logger.info(f"✅ Paid salary: {amount} to {member_name}")
            
            return {
                "success": True,
                "member_id": member_id,
                "member_name": member_name,
                "amount": amount
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to pay salary: {e}")
            return {"success": False, "error": str(e)}
    
    # ==================== DASHBOARD STATS ====================
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard summary statistics.
        
        Returns:
            Dict with dashboard stats
        """
        if not self.db:
            return {"success": False, "error": "Firebase not connected"}
        
        try:
            # Get all data
            clients = list(self.db.collection("clients").stream())
            projects = list(self.db.collection("projects").stream())
            transactions = list(self.db.collection("transactions").stream())
            team = list(self.db.collection("team").stream())
            
            # Calculate stats
            total_income = sum(
                t.to_dict().get("amount", 0)
                for t in transactions
                if t.to_dict().get("type") == "income"
            )
            
            total_expenses = sum(
                t.to_dict().get("amount", 0)
                for t in transactions
                if t.to_dict().get("type") == "expense"
            )
            
            active_clients = sum(
                1 for c in clients
                if c.to_dict().get("status") == "active"
            )
            
            active_projects = sum(
                1 for p in projects
                if p.to_dict().get("status") == "In Progress"
            )
            
            total_team = len(team)
            
            return {
                "success": True,
                "total_clients": len(clients),
                "active_clients": active_clients,
                "total_projects": len(projects),
                "active_projects": active_projects,
                "total_income": total_income,
                "total_expenses": total_expenses,
                "profit": total_income - total_expenses,
                "team_members": total_team
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get dashboard stats: {e}")
            return {"success": False, "error": str(e)}


# Global instance
firebase_client = FirebaseClient()

