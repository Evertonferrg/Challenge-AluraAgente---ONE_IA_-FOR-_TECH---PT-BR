import React, { useState } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import InstitucionalChatPage from './pages/InstitucionalChatPage';
import './App.css';

function App() {
    const [pagina, setPagina] = useState('home');

    return (
        <div className="App">
            <Header aoNavegar={setPagina} />
            {pagina === 'home' && <HomePage />}
            {pagina === 'chat' && <ChatPage />}
            {pagina === 'institucional' && <InstitucionalChatPage />}
            <Footer />
        </div>
    );
}

export default App;