import React from 'react';
import Hero from '../sections/Hero';
import About from '../sections/About';
import Products from '../sections/Products';
import Contact from '../sections/Contact';

const HomePage = () => {
    return (
        <>
            <Hero />
            <About />
            <Products />
            <Contact />
        </>
    );
};

export default HomePage;