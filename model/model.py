from database.parco_DAO import ParcoDAO
from database.escursione_DAO import EscursioneDAO
from database.punto_interesse_DAO import PuntoInteresseDAO
from model.escursione import Escursione


class Model:
    def __init__(self):
        self.escursioni_map = {} # Mappa ID escursione -> oggetti Escursione
        self.punti_interesse_map = {} # Mappa ID punto di interesse -> oggetti PuntoInteresse

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_escursioni()
        self.load_punti_interesse()
        self.load_relazioni()

    @staticmethod
    def load_parchi():
        """ Restituisce tutti i parchi disponibili """
        return ParcoDAO.get_parchi()

    def load_escursioni(self):
        """ Carica tutte le escursioni in un dizionario [id, Escursione]"""
        self.escursioni_map = EscursioneDAO.get_escursioni()

    def load_punti_interesse(self):
        """ Carica tutti i punti di interesse in un dizionario [id, PuntoInteresse]"""
        self.punti_interesse_map = PuntoInteresseDAO.get_punti_interesse()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra escursioni e punti di interesse e salvarle nelle strutture dati
            Collega escursione <-> punti di interesse.
            --> Ogni Escursione ha un set di PuntoInteresse.
            --> Ogni PuntoInteresse ha un set di Escursioni.
        """
        rel = EscursioneDAO.get_escursioni_punti_interesse() #prendo il dizionario delle relazioni
        for riga in rel: #prende una relazione alla volta

            #estraiamo per ogni riga l'id dell'escursione e del punto di interesse
            id_esc = riga["id_escursione"]
            id_pt = riga["id_punto_interesse"]

            #cerco nei relativi dizionari le chiavi grazie agli id e restituisce gli oggetti Escursione e Punto di Interesse
            escursione = self.escursioni_map[id_esc]
            pt_interesse = self.punti_interesse_map[id_pt]

            #accedo all'attributo set dell'oggetto Escursione e inserisco l'oggetto PuntoInteresse in quell'insieme
            escursione.punti_interesse.add(pt_interesse)
            #accedo all'attributo set dell'oggetto PuntoInteresse e inserisco l'oggetto Escursione nel suo insieme
            pt_interesse.escursioni.add(escursione)


    def genera_pacchetto(self, id_parco: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto di escursioni ottimale per un parco rispettando i vincoli di durata, budget e punti di interesse unici.
        :param id_parco: id del parco
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Escursione)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il voto complessivo dei visitatori per il pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        #li salvo con self così che la funzione ricorsione riesca a leggerli
        self.max_giorni = max_giorni
        self.max_budget = max_budget

        self.escursioni_parco = [] #raccolgo solo le escursioni relative al parco che sto considerando
        #prendo tutte le escursioni che ho già in memoria e le controllo una per una
        for esc in self.escursioni_map.values():
            if esc.id_parco == id_parco:
                self.escursioni_parco.append(esc)

        self._ricorsione(0, [], 0, 0, 0, set())

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, punti_usati: set):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il voto complessivo dei visitatori"""

        #condizione di terminazione
        if start_index >= len(self.escursioni_parco): #quando ho finito di valutare le escursioni della lista di uno specifico parco
            if self._valore_ottimo == -1 or valore_corrente > self._valore_ottimo: #verifico il livello di apprezzamento più alto dai visitatori
                self._valore_ottimo = valore_corrente
                self._costo = costo_corrente
                self._pacchetto_ottimo = list(pacchetto_parziale) #copio la lista per salvarla nel pacchetto ottimale
        else:
            # prendo l'escursione nella posizione corrente start_index
            escursione = self.escursioni_parco[start_index]

            # calcolo quanto vale questa singola escursione sommando i voti di tutti i suoi punti di interesse
            voto_escursione = 0
            for punto in escursione.punti_interesse:
                voto_escursione += punto.voto_visitatori

            # specifico i vincoli considerando il costo e la durata totale e verificando che non superi il max
            if costo_corrente+escursione.costo <= self.max_budget or self.max_budget is None:
                if durata_corrente+escursione.durata_giorni <= self.max_giorni or self.max_giorni is None:
                    pacchetto_parziale.append(escursione)
                    costo_corrente += escursione.costo
                    durata_corrente += escursione.durata_giorni
                    valore_corrente += voto_escursione
                    punti_usati.update(escursione.punti_interesse) #aggiorno i valori

                    self._ricorsione(start_index+1, pacchetto_parziale, durata_corrente, costo_corrente, valore_corrente, punti_usati)
                    pacchetto_parziale.pop()
                    costo_corrente -= escursione.costo
                    durata_corrente -= escursione.durata_giorni
                    valore_corrente -= voto_escursione
                    punti_usati -= escursione.punti_interesse #applico il backtracking

            self._ricorsione(start_index + 1, pacchetto_parziale, durata_corrente, costo_corrente, valore_corrente, punti_usati)





