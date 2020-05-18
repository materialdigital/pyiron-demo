from pyiron.base.job.template import TemplateJob
from temmeta import data_io as dio
from temmeta import image_filters as imf


class TEMMETAJob(TemplateJob):
    def __init__(self, project, job_name):
        super(TEMMETAJob, self).__init__(project, job_name) 
        self.input['file_name'] = ''
        self.input['vector'] = []
        self._python_only_job = True
        self._image = None
        self._vec = []
        self._profile = []
    
    @property
    def file_name(self):
        return self.input['file_name']
    
    @file_name.setter
    def file_name(self, file_name):
        self.input['file_name'] = file_name
        self._image = self.create_tem_image()
        
    @property
    def vector(self):
        return self.input['vec']
    
    @file_name.setter
    def vector(self, vector):
        self.input['vector'] = vector
        self._vec = vector
    
    def create_tem_image(self):
        emd1 = dio.EMDFile(self.input['file_name'])
        return emd1.get_dataset("Image", "6fdbde41eecc4375b45cd86bd2be17c0")
    
    def plot(self):
        if len(self._vec) == 2:
            [[x1, y1], [x2, y2]] = self._vec
        av = self._image.average()
        ax, im = av.plot(dpi=50)
        if len(self._vec) == 2:
            ax.arrow(x1, y1, x2-x1, y2-y1, color = (0., 1., 0.), head_width=5)
    
    def run_static(self):
        if len(self._vec) == 2:
            [[x1, y1], [x2, y2]] = self._vec
            av = self._image.average()
            self._profile = av.intensity_profile(x1, y1, x2, y2)
            with self.project_hdf5.open("output/generic") as h5out: 
                 h5out["profile"] = self._profile.data
        self.status.finished = True
            
    def plot_profile(self):
        ax, prof1 = self._profile.plot()
        prof1[0].set_label("Profile")
        ax.legend()
        ax.figure.tight_layout()
