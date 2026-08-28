# Final Project Report - Farm Management System (FMS)

## Discussion

Hello! Let’s talk about the development process of my Farm Management System (FMS) application. While the choice of Flask as the web framework and the use of provided SQL scripts were requirements, there were still many decisions and considerations that shaped the final product.

### Initial Setup and Framework Integration

The use of Flask was specified by the instructor, providing a solid foundation for building the application. One of the early decisions I made was to integrate Flask with Jinja2 templates and Bootstrap for the front-end. Flask’s simplicity and extensibility allowed me to focus on the core functionalities rather than getting bogged down by framework-specific configurations.

### Template Design and User Interface

One of the most significant decisions was designing the templates to ensure a user-friendly and intuitive interface. For instance, in the `stock.html` template, I organized the information to be easily digestible, grouping animals by mobs and displaying essential details such as IDs, ages, DOBs, weights, and providing quick links to edit individual animals. The use of Bootstrap components helped achieve a responsive design that works well on various screen sizes.

### Feature Implementation and Prioritization

When it came to implementing features, I had to prioritize based on the importance and immediate utility of each function. I began with basic CRUD operations for managing paddocks and animals, ensuring these fundamental functionalities were robust. Once these were established, I added more advanced features like moving mobs between paddocks (`move_mobs.html`) and editing animal details (`edit_animal.html`). This incremental approach allowed me to test and refine each feature before integrating it into the larger system.

### Handling Data and Forms

Another critical aspect was handling data inputs and forms. In the `edit_paddocks.html` template, I created forms to edit existing paddocks and add new ones. Ensuring that these forms were properly validated on the client-side helped improve the user experience and reduced the load on the server. For example, I included step attributes for numerical inputs to enforce precision and required attributes to ensure completeness.

### Error Handling and User Feedback

To ensure the application was robust, I focused on error handling and providing meaningful feedback to users. In cases where an operation failed, such as an attempt to move a mob to an invalid paddock, I displayed clear error messages to guide the user towards correcting the issue. This approach was particularly important for maintaining the integrity of the data and preventing confusion.

### Testing and Debugging

Testing was an integral part of the development process. I performed unit tests for individual components and integration tests to verify the interaction between different parts of the application. Debugging involved using Flask’s built-in debugger and Python logging facilities to track down issues and optimize performance. For example, I logged errors that occurred during database operations to diagnose connectivity problems.

### Future Enhancements

Reflecting on the project, there are several areas for future enhancement. Adding real-time updates for animal movements using WebSocket technology could greatly improve the system’s responsiveness. Integrating predictive analytics for animal health based on historical data could provide valuable insights for better farm management practices.

This report aims to give insight into the design decisions and thought processes that influenced the development of the FMS application. Despite the provided requirements, I made numerous decisions that contributed to the final outcome.

---

References:
- Jinja2 Templates Documentation
- Bootstrap Documentation

---

I hope this provides a clear picture of the decisions and considerations that went into the development of the FMS application.