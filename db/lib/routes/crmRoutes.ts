import {Request, Response} from "express";
import { ContactController } from "../controllers/crmController";


export class Routes {     
    public contactController: ContactController = new ContactController();

    public routes(app): void {          
        app.route('/')
        .get((req: Request, res: Response) => {            
            res.status(200).send({
                message: 'GET request successfulll!!!!'
            })
        })
        
        app.route('/healthcheck')
        .get((req: Request, res: Response) => {            
            res.status(200).send({
                message: 'GET request successfulll!!!!'
            })
        })
        
        // Contact 
        app.route('/contact') 
        // GET endpoint 
        .get(this.contactController.getContacts)
                
        // POST endpoint
        .post(this.contactController.addNewContact)

        // get a specific contact
        app.route('/contact/:contactId')
        .get(this.contactController.getContactWithID)
        // update a specific contact
        .put(this.contactController.updateContact)
        // delete a specific contact
        .delete(this.contactController.deleteContact)
        
        // Contact detail
        app.route('/contact/:contactId')
        // get specific contact
        .get((req: Request, res: Response) => {
        // Get a single contact detail            
            res.status(200).send({
                message: 'GET request successfulll!!!!'
            })
        })
        .put((req: Request, res: Response) => {
        // Update a contact           
            res.status(200).send({
                message: 'PUT request successfulll!!!!'
            })
        })
        .delete((req: Request, res: Response) => {       
        // Delete a contact     
            res.status(200).send({
                message: 'DELETE request successfulll!!!!'
            })
        })

        
    }
}
