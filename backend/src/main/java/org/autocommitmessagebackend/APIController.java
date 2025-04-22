package org.autocommitmessagebackend;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
@CrossOrigin("*")
public class APIController {

    @GetMapping("/test")
    public ResponseEntity<String> testAPI() {
        return ResponseEntity.ok("Hello World From Backend");
    }
}
