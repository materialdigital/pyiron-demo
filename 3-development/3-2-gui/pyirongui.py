import numpy as np
import matplotlib.pylab as plt
import pandas as pd
import ipywidgets as widgets
from IPython.display import display


class GUIStructure:
    def __init__(self, project, msg=None):
        self.project = project
        self.msg = msg
        
        self.count = 0
        self.create_btn = widgets.Button(description='Refresh') 
        self.output_plot3d = widgets.Output(layout=widgets.Layout(width='50%', height='100%'))
        self.cubic_ckb = widgets.Checkbox(value=True, description='Cubic')
        self.ortho_ckb = widgets.Checkbox(value=False, description='Orthorombic')

        self.element_drp = widgets.Dropdown(
            options=['Al', 'Fe', 'Mg'],
            value='Al',
            description='Element:'
        )
        self.repeat_drp = widgets.Dropdown(
            options=range(1, 6),
            value=1,
            description='Repeat:'
        )

        self.cubic_ckb.observe(self.refresh, names='value')
        self.ortho_ckb.observe(self.refresh, names='value')
        self.repeat_drp.observe(self.refresh, names='value')
        self.element_drp.observe(self.refresh, names='value')
        self.create_btn.on_click(self.refresh)
        self.refresh()
        
    def gui(self):
        return widgets.HBox([
            widgets.VBox([self.element_drp, self.repeat_drp, self.cubic_ckb, self.ortho_ckb]), # , self.create_btn]), 
            self.output_plot3d])  
        
    def refresh(self, *args):
        try:
            struc = self.project.create_ase_bulk(self.element_drp.value, cubic=self.cubic_ckb.value, orthorhombic=self.ortho_ckb.value).repeat(self.repeat_drp.value)
        except RuntimeError as e:
            with self.output_plot3d:
                self.output_plot3d.clear_output()
                print ('Error: ', e)
                return
        self.structure = struc
        self.view = struc.plot3d()

        self.output_plot3d.clear_output()
        with self.output_plot3d:
            display(self.view) 
            
         
class PARAM_MD:
    def __init__(self, gui_calc):
        self.gui_calc = gui_calc
        
        self.temperature = widgets.IntSlider(description='Temperature: ', min=1, max=5000, steps=10, value=500)
        self.n_ionic_steps = widgets.Dropdown(
            options= [int(10**i) for i in range(8)],
            value=10000,
            description='n_ionic_steps:'
        )
        self.n_print = widgets.Dropdown(
            options= [int(10**i) for i in range(6)],
            value=100,
            description='n_print:'
        ) 
        
    def gui(self):
        self.temperature.observe(self.gui_calc.refresh, names='value')
        self.n_ionic_steps.observe(self.gui_calc.refresh, names='value')
        self.n_print.observe(self.gui_calc.refresh, names='value')
        
        return widgets.VBox([self.temperature, self.n_ionic_steps, self.n_print], layout={'border': '1px solid lightgray'})
    
   
class PARAM_MIN:
    def __init__(self, gui_calc):
        self.gui_calc = gui_calc
    
        self.f_eps = widgets.Dropdown(
            options= [10**(-i) for i in range(5)],
            value=10**(-4),
            description='Force conv.:'
        )

        self.max_iter = widgets.Dropdown(
            options= [int(10**(i)) for i in range(5)],
            value=100,
            description='max iterations:'
        )
        self.n_print = widgets.Dropdown(
            options= [int(10**i) for i in range(6)],
            value=100,
            description='n_print:'
        ) 
        
    def gui(self):
        self.f_eps.observe(self.gui_calc.refresh, names='value')
        self.max_iter.observe(self.gui_calc.refresh, names='value')
        self.n_print.observe(self.gui_calc.refresh, names='value')
        
        return widgets.VBox([self.f_eps, self.max_iter, self.n_print], layout={'border': '1px solid lightgray'})
    
    
def get_generic_inp(job):
    j_dic = job['input/generic/data_dict']
    return {k:v for k,v in zip(j_dic['Parameter'], j_dic['Value'])}


class GUI_CALC:
    def __init__(self, gui_structure):
        self.gui_structure = gui_structure
        
        self.project = self.gui_structure.project
        self.msg = self.gui_structure.msg
        
        self.par_md = PARAM_MD(self)
        self.par_min = PARAM_MIN(self)
        
        calc_opt = widgets.Tab()
        calc_opt.set_title(0, 'MD')
        calc_opt.set_title(1, 'Minimize')
        calc_opt.set_title(2, 'Static')

        calc_opt.children = [self.par_md.gui(), self.par_min.gui(), widgets.VBox()] 
        self.calc_opt = calc_opt
        
        self.output = widgets.Output(layout=widgets.Layout(width='50%', height='100%'))

        self.job_name = widgets.Text(
            value='',
            placeholder='Type something',
            description='Job Name:',
            disabled=False
        )

        self.create_btn = widgets.Button(description='Refresh')
        self.run_btn = widgets.Button(description='Run')
        self.run_btn.style.button_color ='lightblue'

        self.job_type = widgets.Dropdown(
            options = ['Lammps', 'Vasp'],
            value='Lammps',
            description='Job Type:'
        )

        self.potential = widgets.Dropdown(
            options = [''], #job.list_potentials(),
    #         value='Lammps',
            description='Potential:'
        )
        
    def set_job_params(self, job):
        self.struc = job.get_structure(-1)  # TODO: i_frame
        self.potential.options = self.job.list_potentials()  
        self.potential.value = job.potential['Name'].values[0]
        generic_par = get_generic_inp(job)
        if generic_par['calc_mode'] == 'md':
            with self.msg:
                print ('Temp: ', generic_par['temperature'])
            self.par_md.temperature = generic_par['temperature']
            self.par_md.n_ionic_steps = generic_par['n_ionic_steps'] 
    
    def refresh_input(self, *args):
        if self.struc is None:
            with self.output:
                print ('No structure')
            return widgets.HBox([self.output])    

        if self.job_name.value == "":
            self.job_name.value = self.struc.get_chemical_formula()    

        self.job = self.project.create_job(self.job_type.value, self.job_name.value)
#         if self.job.status == 'finished':
#             self.set_job_params(self.job)
#         else:    
        self.job.structure = self.struc
        self.potential.options = self.job.list_potentials()     
        
    def refresh(self, job=None, *args):
#         if job is None:
        self.struc = self.gui_structure.structure
        self.view = self.gui_structure.view
        self.job_name.value = self.struc.get_chemical_formula() 

        self.refresh_input()
        self.refresh_job_name()
        
    def refresh_job_name(self, *args):     
        pr = self.project
            
        self.output.clear_output()    
        if self.job_name.value in pr.list_nodes():
            self.run_btn.style.button_color ='red'
            self.run_btn.description = 'Delete'
            with self.output:
#                     print ("test: ", job_name.value, pr.list_nodes(), job_name.value in pr.list_nodes(), run_btn.style.button_color)                      
                self.job = pr.load(self.job_name.value)
                display(self.job.animate_structure())  
        else:
            self.run_btn.style.button_color ='lightgreen'
            self.run_btn.description = 'Run'
            with self.output:
                display(self.view)  
#                 print ("test: ", self.job_name.value, pr.list_nodes(), self.job_name.value in pr.list_nodes(), self.run_btn.style.button_color)    
            
    def on_run_btn_clicked(self, b):
        if b.description == 'Run':
            self.job.potential = self.potential.value
            if self.job_type.value == 'MD':
                self.job.calc_md(temperature=self.par_md.temperature.value, n_ionic_steps=self.par_md.n_ionic_steps.value, n_print=self.par_md.n_print.value)
            elif self.job_type.value == 'Minimize': 
                self.job.calc_minimize(f_eps=self.par_min.f_eps.value, max_iter=self.par_min.max_iter.value, n_print=self.par_min.n_print.value)
            else:
                self.job.calc_static()
            self.job.run()
            self.refresh()
        elif b.description == 'Delete':
            self.job.remove()
            self.refresh()
            
    def gui(self):
        self.job_type.observe(self.refresh, names='value')
        self.job_name.on_submit(self.refresh_job_name)
        self.potential.observe(self.refresh, names='value')

        self.create_btn.on_click(self.refresh)   
        self.run_btn.on_click(self.on_run_btn_clicked)
        job_box = widgets.VBox([self.job_type, self.job_name, self.potential], layout={'border': '1px solid lightgray'})

        return widgets.HBox([widgets.VBox([self.calc_opt, job_box, self.create_btn, self.run_btn]), self.output])
    
    
class GUI_EXPLORER:
    def __init__(self, project, msg=None):
        self.project = project
        self.msg = msg
        
        self.output = widgets.Output(layout=widgets.Layout(width='50%', height='100%'))        
        self.groups = widgets.Select(options=[], description='Group:')
        self.nodes = widgets.Select(options=[], description='Nodes:')
        self._update()

        self.groups.observe(self.refresh_group, names='value')
        self.nodes.observe(self.refresh_node, names='value')
        
    def refresh(self, *args):
        pass
    
    @property
    def structure(self):
        if self.view is not None:
            return self.node.get_structure(self.view.frame)
        
    def gui(self):
        return widgets.HBox([
            widgets.VBox([self.groups, self.nodes]), 
            self.output])  
    
    def _update(self):
        groups = [".", ".."] + self.project.list_groups()
        nodes = ["."] + self.project.list_nodes()
        self.groups.options = groups
        self.nodes.options = nodes        
        
    def refresh_group(self, *args):
        if self.groups.value != '.':
            self.project = self.project[self.groups.value]
            self._update() 

    def refresh_node(self, *args):
        self.view = None
        if self.nodes.value is not None:
            node = self.project[self.nodes.value] 
            if hasattr(node, 'animate_structure'):
                self.output.clear_output()
                with self.output:
                    print ('animate')
                    self.view = node.animate_structure()
                    display(self.view)
                    self.node = node
            elif hasattr(node, 'list_groups'):
                self.project = node 
                self._update()                     
                
                
class GUI_PYIRON:    
    def __init__(self, project):
        self.msg = widgets.Output(layout={'border': '1px solid black'})
        self.msg.append_stdout('')
        self.msg.append_stderr('')
        self.clear_msg = widgets.Button(description='Clear')
        
        self.gui_structure = GUIStructure(project=project, msg=self.msg)
        self.gui_calc = GUI_CALC(self.gui_structure)
        self.gui_explorer = GUI_EXPLORER(project)
        
    def on_clear_msg_clicked(self, b):
        self.msg.clear_output()
        
    def gui(self):

        tab = widgets.Tab()
        tab.set_title(0, 'Structure')
        tab.set_title(1, 'Calculate')
        tab.set_title(2, 'Explorer')
        tab.children = [self.gui_structure.gui(), self.gui_calc.gui(), self.gui_explorer.gui()]
        
        self.tab_children = [self.gui_structure, self.gui_calc, self.gui_explorer]
        
        def on_value_change(change):
            sel_ind = change['new']
            self.msg.clear_output()
            with self.msg:
                print (sel_ind, type(tab.children[sel_ind]), hasattr(self.tab_children[sel_ind], 'refresh'))
            self.tab_children[sel_ind].refresh()
            
            
        self.clear_msg.on_click(self.on_clear_msg_clicked)
        tab.observe(on_value_change, names='selected_index')
        return widgets.VBox([tab, widgets.HBox([self.msg, self.clear_msg])], layout={'border': '4px solid lightgray'})