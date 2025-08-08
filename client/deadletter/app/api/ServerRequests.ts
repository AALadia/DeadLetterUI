/* eslint-disable @typescript-eslint/no-explicit-any */
import Server from "./Server";
import type { Id, Version, Topicname, Subscribername, Endpoint, Errormessage, Retrycount, Status, Createdat, Lasttriedat, DeadLetter, Originalmessage } from '../schemas/DeadLetterSchema.ts';
import type { Name, Email, Password, Id1, Value, Description, Collectionstransacted, Unauthorizedmessage, UserRoles, Usertype, User, Role } from '../schemas/UserSchema.ts';

    class ServerRequests extends Server {
    constructor() {
        super();
    }

    
    async setUserRole(userIdToChangeRole: string, userType: string, userId: string): Promise<any> {
        try {
        const res = await fetch(`${this.apiUrl}/setUserRole`, {
            method: 'POST',
            headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({"userIdToChangeRole": userIdToChangeRole, "userType": userType, "userId": userId}),
            cache: 'no-store'
        });
        const data = await res.json();
        
        return data;
        } catch (error) {
            console.error("Error:", error);
            return {"message": "Failed to fetch data", "error": error};
        }
    }

    async setSpecificRoles(userIdToChangeRole: string, roleId: string, value: boolean, userId: string): Promise<any> {
        try {
        const res = await fetch(`${this.apiUrl}/setSpecificRoles`, {
            method: 'POST',
            headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({"userIdToChangeRole": userIdToChangeRole, "roleId": roleId, "value": value, "userId": userId}),
            cache: 'no-store'
        });
        const data = await res.json();
        
        return data;
        } catch (error) {
            console.error("Error:", error);
            return {"message": "Failed to fetch data", "error": error};
        }
    }

    async fetchUserList(projection: Object): Promise<any> {
        try {
        const res = await fetch(`${this.apiUrl}/fetchUserList`, {
            method: 'POST',
            headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({"projection": projection}),
            cache: 'no-store'
        });
        const data = await res.json();
        
        return data;
        } catch (error) {
            console.error("Error:", error);
            return {"message": "Failed to fetch data", "error": error};
        }
    }

    async createDeadLetter(id: string, originalMessage: Object, topicName: string, subscriberName: string, endpoint: string, errorMessage: string): Promise<any> {
        try {
        const res = await fetch(`${this.apiUrl}/createDeadLetter`, {
            method: 'POST',
            headers: {
            "Content-Type": "application/json",
            
            },
            body: JSON.stringify({"id": id, "originalMessage": originalMessage, "topicName": topicName, "subscriberName": subscriberName, "endpoint": endpoint, "errorMessage": errorMessage}),
            cache: 'no-store'
        });
        const data = await res.json();
        
        return data;
        } catch (error) {
            console.error("Error:", error);
            return {"message": "Failed to fetch data", "error": error};
        }
    }

    async replayDeadLetter(deadLetterId: string, userId: string): Promise<any> {
        try {
        const res = await fetch(`${this.apiUrl}/replayDeadLetter`, {
            method: 'POST',
            headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({"deadLetterId": deadLetterId, "userId": userId}),
            cache: 'no-store'
        });
        const data = await res.json();
        
        return data;
        } catch (error) {
            console.error("Error:", error);
            return {"message": "Failed to fetch data", "error": error};
        }
    }

    async loginWithGoogle(firebaseUserObject: Object): Promise<any> {
        try {
        const res = await fetch(`${this.apiUrl}/loginWithGoogle`, {
            method: 'POST',
            headers: {
            "Content-Type": "application/json",
            
            },
            body: JSON.stringify({"firebaseUserObject": firebaseUserObject}),
            cache: 'no-store'
        });
        const data = await res.json();
        localStorage.setItem("access_token", data.access_token)
        return data;
        } catch (error) {
            console.error("Error:", error);
            return {"message": "Failed to fetch data", "error": error};
        }
    }

    async mockPost(message: Object): Promise<any> {
        try {
        const res = await fetch(`${this.apiUrl}/mockPost`, {
            method: 'POST',
            headers: {
            "Content-Type": "application/json",
            
            },
            body: JSON.stringify({"message": message}),
            cache: 'no-store'
        });
        const data = await res.json();
        
        return data;
        } catch (error) {
            console.error("Error:", error);
            return {"message": "Failed to fetch data", "error": error};
        }
    }

    async listDeadLetters(filter: Record<string, unknown> = {}, projection: Record<string, number> | null = null): Promise<any> {
        try {
        const res = await fetch(`${this.apiUrl}/listDeadLetters`, {
            method: 'POST',
            headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({ filter, projection }),
            cache: 'no-store'
        });
        const data = await res.json();
        
        return data;
        } catch (error) {
            console.error("Error:", error);
            return {"message": "Failed to fetch data", "error": error};
        }
    }

}

export default ServerRequests;
