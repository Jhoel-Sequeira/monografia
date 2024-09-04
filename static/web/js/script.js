let loginForm = document.querySelector('.header .login-form');
let registerForm = document.querySelector('.header .register-form');
let todo = document.getElementById('todo');
function log(){
    loginForm.classList.toggle('active');
    if ($('#registro').is(':visible')){
        registerForm.classList.toggle('active');
        todo.style.filter = "blur(0px)";
        navbar.classList.add('active');
        
    }else{
        
        todo.style.filter = "blur(0px)";
        // navbar.classList.remove('active');
    }
    navbar.classList.add('active');
    window.onscroll = () =>{
        loginForm.classList.remove('active');
        if(window.scrollY > 0){
            document.querySelector('.header').classList.add('active');
        }else{
            document.querySelector('.header').classList.remove('active');
        }
        navbar.classList.remove('active');
    }
}
$('#register-btn').click(function(){
        registerForm.classList.toggle('active');
        
        
        if ($('#login').is(':visible')){
            loginForm.classList.toggle('active');
        }else{
            
            todo.style.filter = "blur(0px)";
        }
        todo.style.filter = "blur(5px)";
        navbar.classList.remove('active');
        window.scrollTo(0,0);
})
// document.querySelector('#register-btn2').onclick = () =>{
//     loginForm.classList.toggle('active');
//     registerForm.classList.toogle('active');
    
//     navbar.classList.remove('active');
// }


let navbar = document.querySelector('.header .navbar');

document.querySelector('#menu-btn').onclick = () =>{
    navbar.classList.toggle('active');    
    loginForm.classList.remove('active');
    registerForm.classList.remove('active');
}

window.onscroll = () =>{
    navbar.classList.remove('active');
    if(window.scrollY > 0){
        document.querySelector('.header').classList.add('active');
    }else{
        document.querySelector('.header').classList.remove('active');
    }
}

window.onload = () =>{
    if(window.scrollY > 0){
        document.querySelector('.header').classList.add('active');
    }else{
        document.querySelector('.header').classList.remove('active');
    }
}