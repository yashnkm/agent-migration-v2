package com.example.demo.service;

import com.example.demo.entity.Employee;
import com.example.demo.repository.EmployeeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;

@Service
public class EmployeeService {

    @Autowired
    private EmployeeRepository employeeRepository;

    public Employee createEmployee(Employee employee) {
        // Validate email
        if (employeeRepository.existsByEmail(employee.getEmail())) {
            throw new RuntimeException("Email already exists");
        }

        // Set default department if null
        if (employee.getDepartment() == null) {
            employee.setDepartment("General");
        }

        // Validate minimum salary
        if (employee.getSalary() != null && employee.getSalary() < 30000) {
            throw new RuntimeException("Minimum salary is 30000");
        }

        return employeeRepository.save(employee);
    }

    public Employee updateEmployee(Long id, Employee employeeDetails) {
        Optional<Employee> employeeOpt = employeeRepository.findById(id);

        if (!employeeOpt.isPresent()) {
            throw new RuntimeException("Employee not found");
        }

        Employee employee = employeeOpt.get();
        employee.setName(employeeDetails.getName());
        employee.setEmail(employeeDetails.getEmail());
        employee.setDepartment(employeeDetails.getDepartment());
        employee.setSalary(employeeDetails.getSalary());

        return employeeRepository.save(employee);
    }

    public Employee getEmployeeById(Long id) {
        return employeeRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Employee not found"));
    }

    public List<Employee> getAllEmployees() {
        return employeeRepository.findAll();
    }

    public void deleteEmployee(Long id) {
        employeeRepository.deleteById(id);
    }

    public Double calculateSalary(Long id) {
        Employee employee = getEmployeeById(id);
        Double baseSalary = employee.getSalary();

        // Apply tax deduction (20%)
        Double afterTax = baseSalary * 0.8;

        return afterTax;
    }
}
