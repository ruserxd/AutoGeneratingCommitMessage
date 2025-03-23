package com.example.commitmessagegenerator.Service;

public class UserService1 {
    public String getUserName(int userId) {
        return "-" + userId + "-v1";
    }
    public int getUserAge(int userId) {
        return userId + 20;
    }
}